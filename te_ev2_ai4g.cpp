#include <iostream>
#include <unistd.h>
#include <fstream>
#include <sstream>
#include <vector>
#include "opencv2/core/core.hpp"
#include <opencv2/opencv.hpp>
#include <iomanip>
#include <chrono>
#include "i3system_TE.h"

using namespace i3;
using namespace std;
using namespace cv;
void DeviceChangedCallback(TE_STATE _in);
hotplug_callback_func gCallback;

void _print(const std::string& message) {
    // Obtener el tiempo actual
    auto now = std::chrono::system_clock::now();
    
    // Convertir a time_t
    auto now_c = std::chrono::system_clock::to_time_t(now);
    
    // Usar un stringstream para formatear la fecha y hora
    std::stringstream ss;
    ss << std::put_time(std::localtime(&now_c), "[%d/%m/%Y - %H:%M:%S]");
    
    // Imprimir el mensaje formateado
    std::cout << ss.str() << " :: TIR_images :: " << message << std::endl;
}

int main(int argc, char* argv[])	//argv is count of arguments plus current exec file
{
    //preparation to count loops to read only relevant frames
    int count_Skipframes = 0;
    int countFrames = 0;
    int nbrFramesToSkip = 30;
    bool FileNew = 0;
    int nbrCapturedFrames = 4;
    
    string outDirectory = "/home/pi/thermalcamera/thermal_images/";
	string filePrefix = "default_prefix";
    
    unsigned shutterTime = 3; //x * 30 seconds, i.e., every 2 minutes
	_print("Starting TIR images software (C++)");

    // vector<string> wholeTerminalArgs;
    if (argc > 1){
	outDirectory = argv[1];
	////cout << outDirectory << endl;
    nbrCapturedFrames = atoi(argv[2]);
	filePrefix = argv[3];

	// wholeTerminalArgs.assign(argv + 1, argv + argc);
	// //cout << wholeTerminalArgs[0] << endl;
    }
    else{
	////cout << "using standard values..." << endl;
    }

    // Set Hotplug Callback Function
    gCallback = &DeviceChangedCallback;
    SetHotplugCallback(gCallback);
    
    // Scan connected TE.
    SCANINFO *pScan = new SCANINFO[MAX_USB_NUM];
    ScanTE(pScan);
    int hnd_dev = -1;
    for(int i = 0; i < MAX_USB_NUM; i++){
        if(pScan[i].bDevCon){
            hnd_dev = i;
            break;
        }
    }
    delete pScan;

    // Open Connected Device
    if(hnd_dev != -1){
        TE_A *pTE = OpenTE_A(hnd_dev);
        bool exit = false;
                
        if(pTE){
            ////cout << "TE Opened" << endl;
            
            //Set shutter mode
            if(pTE->SetShutterMode(I3_TIME_SHUTTER)){
                ////cout << "Shutter mode set to time" << endl;
                if(pTE->SetShutterMode(I3_TIME_SHUTTER)){   
                    ////cout << "Shutter mode set to " << shutterTime << endl;
                }
            }

            // Read Flash Data
            ////cout << "Read image data" << endl;
            int width = pTE->GetImageWidth();
            int height = pTE->GetImageHeight();
            int size = width * height;
            ////cout << width << "; " << height << endl;
            
            //setup array with length of pixel numbers
            unsigned short *pImgBuf = new unsigned short[size];
            unsigned short *imgTemp = new unsigned short[size];	
            unsigned short *imgNoAGC = new unsigned short[size];
            unsigned short *imgTempNoAGC = new unsigned short[size];
            unsigned short *imgTempRange = new unsigned short[size];
            unsigned short *tempRange = new unsigned short[size];
            float *tempFloat = new float[size]; 
            float *tempFloatNoAGC = new float[size];
            float *tempFloatRange = new float[size];
            
            float tempMin = -15;
            float tempMax = 40;

            for(int i = 1; i < nbrCapturedFrames + nbrFramesToSkip; ++i){
                        
                //skip first "garbage" frames before starting to read
                count_Skipframes = count_Skipframes + 1;
                //cout << count_Skipframes << endl;
                if (count_Skipframes < nbrFramesToSkip){
                    if(pTE->RecvImage(pImgBuf, true) == 1){
                        //cout << pImgBuf[0] << endl;
                        //cout << "Skipping frames " << count_Skipframes << " out of " << nbrFramesToSkip << endl;		
                    }
                    usleep(110000);
                    continue;
                }
                
                stringstream iStr;
                iStr << countFrames;
                
                //Capture and save DN and temperature image with AGC
                bool received = false;
                while (not received){
                    if (pTE->RecvImage(pImgBuf, true) == 1) {
                        pTE->CalcTemp(imgTemp);
                        received=true;
                    }
                }
                
                //get temperature values per pixel
                //for (int i = 0; i < size; ++i){
                //    tempFloat[i] = static_cast<float>((imgTemp[i] - 5000) / 100.0f);
                //}
                
                //Save 16 bit
                //Mat img16_temp(height, width, CV_32FC1, tempFloat);                
                //string outImage_temp_16 = outDirectory + "temperature_16_" + iStr.str() + ".tif";
                //bool result = imwrite(outImage_temp_16, img16_temp);
                //if (result){
                //    //cout << "temperature image 16 bit saved" << endl;
                //} else {
                //    //cout << "Failed to save temperature image 16 bit!" << endl;
                //}
                
                Mat img16(height, width, CV_16UC1, pImgBuf);                
                string outImage_DN_16 = outDirectory + filePrefix + "DN_16_" + iStr.str() + ".tif";
                bool result_1 = imwrite(outImage_DN_16, img16);
                if (result_1){
                    //cout << "DN image 16 bit saved" << endl;
                } else {
                    //cout << "Failed to save the DN image 16 bit!" << endl;
                }
                
                //Capture and save DN and temperature image without AGC
                bool received_noAGC = false;
                while (not received_noAGC){
                    if (pTE->RecvImage(imgNoAGC, false) == 1) {
                        pTE->CalcTemp(imgTempNoAGC);
                        received_noAGC=true;
                    }
                }
                
                //get temperature values per pixel
                //for (int i = 0; i < size; ++i){
                //    tempFloatNoAGC[i] = static_cast<float>((imgTempNoAGC[i] - 5000) / 100.0f);
                //}
                
                //save images
                //Mat imgOrig_16_temp(height, width, CV_32FC1, tempFloatNoAGC);                
				//string outImage_temp_noAGC_16 = outDirectory + "temperature_noAGC_16_" + iStr.str() + ".tif"; 
                //bool result_2 = imwrite(outImage_temp_noAGC_16, imgOrig_16_temp);   
                //if (result_2){
                //    //cout << "temperature no AGC image 16 bit saved" << endl;
                //} 
                //else {
                //    //cout << "Failed to save the temperature no AGC image 16 bit!" << endl;
                //}
                
                Mat imgOrig_16(height, width, CV_16UC1, imgNoAGC);                
                string outImage_DN_noAGC_16 = outDirectory + filePrefix + "DN_noAGC_16_" + iStr.str() + ".tif";
                bool result_3 = imwrite(outImage_DN_noAGC_16, imgOrig_16);   
                if (result_3){
                    //cout << "DN no AGC image 16 bit saved" << endl;
                } 
                else {
                    //cout << "Failed to save the DN no AGC image 16 bit!" << endl;
                }
                
                float gain = 0.2f, offset = -1500.f;
                
                //Get image in specific temperature range
                bool received_tempRange = false;
                while (not received_tempRange){
                    if (pTE->RecvImage(imgTempRange, tempMin, tempMax) == 1) {
                        pTE->CalcTemp(tempRange);
                        received_tempRange=true;
                    }
                }

                //get temperature values per pixel
                for (int i = 0; i < size; ++i){
                    tempFloatRange[i] = static_cast<float>((tempRange[i] - 5000) / 100.0f);
                }
                
                Mat img_tempRange_temp(height, width, CV_32FC1, tempFloatRange);                
				string outImage_tempRange = outDirectory + filePrefix + "temperature_tempRange_16_" + iStr.str() + ".tif"; 
                bool result_4 = imwrite(outImage_tempRange, img_tempRange_temp);   
                if (result_4){
                    //cout << "temperature Range image 16 bit saved" << endl;
                } 
                else {
                    //cout << "Failed to save temperature Range image 16 bit!" << endl;
                } 
                
                Mat img_tempRange(height, width, CV_16UC1, imgTempRange);                
                string outImage_DN_tempRange = outDirectory + filePrefix + "DN_tempRange_16_" + iStr.str() + ".tif";
                bool result_5 = imwrite(outImage_DN_tempRange, img_tempRange);   
                if (result_5){
                    //cout << "DN temperature Range image 16 bit saved" << endl;
                } 
                else {
                    //cout << "Failed to save the DN temperature Range image 16 bit!" << endl;
                }
               
                //Get temperatures
                float fpaTemp = pTE->GetFpaTemp();
                //cout << "FPA temperature = " << fpaTemp << endl;
                
                //Get shutter temperatures raw
                unsigned short shutterTempRaw = pTE->GetShutterPt100RawValue();
                //cout << "Shutter temperature raw = " << shutterTempRaw << endl;
                
                //Get shutter temperatures
                float shutterTemp = pTE->GetShutterPt100Temp();
                //cout << "Shutter temperature = " << shutterTemp << endl;
                
                // Get Temperature at (x, y)
                int x = 320, y = 240;
                float t = tempFloatRange[y*width + x]; //imgTemp[x*y]                    
                //cout << "Temperature center pixel = " << t << endl;
                //delete imgTemp;
                
                //Write temperatures to files
                ofstream outTxtTemp;
                string outfileTempTxt = outDirectory + filePrefix + "temperatures.txt";
                const char *outputTemptxt = outfileTempTxt.c_str();

                // if first loop create file and if afterwards solely append in file
                if (FileNew == 0){
                    outTxtTemp.open(outputTemptxt);
                    FileNew = 1;
                }
                else{
                    outTxtTemp.open(outputTemptxt, ios_base::app);
                }			    
                outTxtTemp << "count " << countFrames << " ";
                outTxtTemp << "FPA_T " << fpaTemp << " ";
                outTxtTemp << "Shutter_T_raw " << shutterTempRaw << " ";
                outTxtTemp << "Shutter_T " << shutterTemp << " ";
				outTxtTemp << "centrePixel_T " << t << endl;
                outTxtTemp.close();                

                countFrames = countFrames + 1;    
                usleep(110000);
				_print("Capturing image " + std::to_string(countFrames) + "/" + std::to_string(nbrCapturedFrames) + " - Central temp: " + std::to_string(t) + " °C");
            }
                
            // Close Device
            pTE->CloseTE();
			_print("C++ Process finished successfully -> Back to .py code");
            //cout << "Close Usb" << endl;
        }
        else{
            //cout << "Access camera failed" << endl;
			_print("ERROR: Access camera failed");
        }          
    }
    else{
        //cout << "Device not connected" << endl;
		_print("ERROR: Device not connected");
    }
    return 0;
	
}
// Callback function executed when TE is arrived to or removed from usb port.
void DeviceChangedCallback(TE_STATE _in){
    if(_in.nUsbState == TE_ARRIVAL){
        // Do something ...
    }
    else if(_in.nUsbState == TE_REMOVAL){
        // Do something ...
    }
}