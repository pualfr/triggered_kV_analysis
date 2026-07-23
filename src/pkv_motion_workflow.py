# -*- coding: utf-8 -*-
"""
Created on Mon May  5 09:49:40 2025
spider version 5
Python 3.12.4
@author: Quentin Léo Techer
"""
# Importing libraries

# File management and traversal
from pathlib import Path
import os 
# Graphics 
import matplotlib.pyplot as plt
# Reading DICOM files
from pydicom import dcmread 
# Program verification
from loguru import logger
# DRR generation
import SimpleITK as sitk
from diffdrr.data import read
from diffdrr.drr import DRR
from diffdrr.visualization import plot_drr
import torch

# Image management
import tifftools
from PIL import Image
from skimage import io
from skimage.exposure import match_histograms, equalize_adapthist
from skimage.registration import phase_cross_correlation
# Generate report
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import numpy as np
from io import BytesIO
import tkinter as tk
from tkinter import ttk
import pandas as pd
import cv2
import csv
import time

import sys


# #########################################################################################################################################
def extract_UID_pCT(path):
    """
    Description: takes as input the path of the folder containing the CT images
    returns the information necessary for the UID check.
    
    input: path(str)
    output: pCT_Frame_of_Reference_UID(list), pCT_Series_Instance_UID(list), pCT_SOP_Instance_UID(list), pCT_Study_Instance_UID(list).
    
    """ 
    L=os.listdir(path)
    pCT_Frame_of_Reference_UID=[]
    pCT_Study_Instance_UID=[]
    pCT_Series_Instance_UID=[]
    pCT_SOP_Instance_UID=[]
    for i in L:
        ds = dcmread(path +"/"+ i)
        pCT_Frame_of_Reference_UID.append(ds.FrameOfReferenceUID) 
        pCT_Study_Instance_UID.append(ds.StudyInstanceUID)
        pCT_Series_Instance_UID.append(ds.SeriesInstanceUID)
        pCT_SOP_Instance_UID.append(ds.SOPInstanceUID) 
    return pCT_Frame_of_Reference_UID,pCT_Series_Instance_UID,pCT_SOP_Instance_UID,pCT_Study_Instance_UID
    
######################################################################################################### 
def extract_UID_RTS(path):
    """
    Description: takes as input the path of the folder containing the RTStruct
    returns the information necessary for the UID check.
    
    input: path(str)
    output: RTS_Frame_of_Reference_UID(list), RTS_Series_Instance_UID(list), RTS_Reference_SOP_Instance_UID(list), RTS_SOP_Instance_UID(list),
           RTS_Reference_SOP_Instance_UID_pS(list)
    
    """
    L=os.listdir(path)
    RTS_Frame_of_Reference_UID=[]
    RTS_Series_Instance_UID=[]
    RTS_Reference_SOP_Instance_UID=[]
    RTS_SOP_Instance_UID=[]
    RTS_Reference_SOP_Instance_UID_pS=[]
    for i in L:
        ds = dcmread(path +"/"+ i)
        RTS_Frame_of_Reference_UID.append(ds.FrameOfReferenceUID) 
        RTS_SOP_Instance_UID.append(ds.SOPInstanceUID)
        # Path to access RTS_Reference_SOP_Instance_UID, RTS_Reference_SOP_Instance_UID_pS, and RTS_Series_Instance_UID
        h=ds.ReferencedFrameOfReferenceSequence[0]
        h=h.RTReferencedStudySequence[0]
        RTS_Reference_SOP_Instance_UID_pS.append(h.ReferencedSOPInstanceUID)
        h=h.RTReferencedSeriesSequence[0]
        RTS_Series_Instance_UID.append(h.SeriesInstanceUID)
        h=h.ContourImageSequence
        for j in range(len(h)):
            RTS_Reference_SOP_Instance_UID.append(h[j].ReferencedSOPInstanceUID)
    return RTS_Frame_of_Reference_UID,RTS_Series_Instance_UID,RTS_Reference_SOP_Instance_UID,RTS_SOP_Instance_UID,RTS_Reference_SOP_Instance_UID_pS

########################################################################################################
def extract_UID_RTP(path):
    """
    Description: takes as input the path of the folder containing the RTP data
    returns the information necessary for the UID check.
    
    input: path(str)
    output: RTP_Instance_UID(list), RTP_Reference_Structure_Set_Sequence(list).
    
    """
    L=os.listdir(path)
    RTP_Reference_Structure_Set_Sequence=[]
    RTP_Instance_UID=[]
    for i in L:
        ds = dcmread(path +"/"+ i)
        h=ds.ReferencedStructureSetSequence[0]
        RTP_Reference_Structure_Set_Sequence.append(h.ReferencedSOPInstanceUID)
        RTP_Instance_UID.append(ds.SOPInstanceUID)
    return  RTP_Instance_UID,RTP_Reference_Structure_Set_Sequence
######################################################################################################### 

def extract_UID_pkV(path):
    """
    Description: takes as input the path of the folder containing the pkV images
    returns the information necessary for the UID check.
    
    input: path(str)
    output: RTP_Reference_SOP_Instance_UID(list)
    
    """

    L=os.listdir(path)
    RTP_Reference_SOP_Instance_UID=[]
    for i in L:
        ds = dcmread(path +"/"+ i)
        h=ds.ReferencedRTPlanSequence[0]
        RTP_Reference_SOP_Instance_UID.append(h.ReferencedSOPInstanceUID)
    return RTP_Reference_SOP_Instance_UID

#########################################################################################################
def check_pkV_RTP(UID_kV,UID_RTP):
    """
    Description: takes as input UID information relating to the patient from the pkV and RTPlan
    returns True if the UID information matches, False otherwise.
    
    input: UID_kV(list), UID_RTP(tuple)
    output: True/False (bool)
    
    """
    for i in UID_kV:
        for j in UID_RTP[0]:
            if i!=j:
                print (i,j)
                return False
    return True

#########################################################################################################
def check_RTP_RTS(UID_RTP,UID_RTS):
    """
    Description: takes as input UID information relating to the patient from the pkV and RTPlan
    returns True if the UID information matches, False otherwise.
    
    input: UID_RTS(tuple), UID_RTP(tuple)
    output: True/False (bool)
    
    """
    for i in UID_RTP[1]:
        if i not in UID_RTS[3]:
            return False
    return True

#########################################################################################################
def check_RTS_CT(UID_pCT,UID_RTS):
    """
    Description: takes as input UID information relating to the patient from the pCT and RTS
    returns True if the UID information matches, False otherwise.
    
    input: UID_RTS(tuple), UID_pCT(tuple)
    output: True/False (bool)
    
    """
    for i in range(len(UID_pCT[0])):
        if UID_pCT[0][i] != UID_RTS[0][0]:
            return False
    for i in range(len(UID_pCT[1])):
        if UID_pCT[1][i] != UID_RTS[1][0]:
            return False
    for i in range(len(UID_pCT[2])):
        if UID_pCT[2][i] not in UID_RTS[2]:
            return False
    for i in range(len(UID_pCT[3])):
        if UID_pCT[3][i] != UID_RTS[4][0]:
            return False
    return True
#########################################################################################################
def full_check(path_pCT,path_RTP,path_pkV,path_RTS):
    """
    Description: takes as input the paths of the folders containing the information necessary for the UID verification.
    performs the verification and returns True if it is valid, False if one of the elements is incorrect.
    
    input: path_pCT (str), path_RTP (str), path_pkV (str), path_RTS (str)
    output: True/False (bool)
    
    """
    UID_RTS=extract_UID_RTS(path_RTS)
    UID_kV=extract_UID_pkV(path_pkV)
    UID_RTP=extract_UID_RTP(path_RTP)
    UID_pCT=extract_UID_pCT(path_pCT)
    if check_RTP_RTS(UID_RTP, UID_RTS) is False:
        print("One of the UIDs does not match between RTP and RTS")
        return False
    if check_RTS_CT(UID_pCT, UID_RTS) is False:
        print("One of the UIDs does not match between pCT and RTS")
        return False
    if check_pkV_RTP(UID_kV, UID_RTP) is False:
        print("One of the UIDs does not match between RTP and pkV")
        return False
    print ("UID verification completed, everything matches") 
    return True
#########################################################################################################
def extract_angle_pkV(path,output_path, reuse_drr=True):
    """
    Description: takes as input the path of the folder containing the kV images during treatment
    returns the list of the acquisition angle for each file present in the folder, as well as the Source Imager Distances,
    the number of angles in each pkV, the first occurrence that uses the following sid, the beam name and the beam number
    +
    Extracts the images from the pkV and saves them as .tif in the pkslice folder.
    
    input: path(str)
    output: var_i (list), sid (list), npkV(list), firstforsid(list), Label(list), RefBeamNumber
    
    """
    var_i=[]
    L=os.listdir(path)
    sid=[]
    k=0
    firstforsid=[]
    npkV=[]
    RefBeamNumber=[]
    logger.debug(f"Start of pkV image extraction")
    for i in L:
        ds = dcmread(path+"/" + i)
        h=ds.ExposureSequence
        ds = dcmread(path_pkV+"/" + i)
        # Extraction of images from pkV
        if len(ds.pixel_array[0].shape)==2:
            for i, slice in enumerate(ds.pixel_array):
                if (not reuse_drr):
                    cv2.imwrite(output_path+"/pkslice/DRR_isocal_fourni_slice_"+str(k)+".tif",slice)
                k+=1
            firstforsid.append(k)
        else:
            if (not reuse_drr):
                cv2.imwrite(output_path+"/pkslice/DRR_isocal_fourni_slice_"+str(k)+".tif",ds.pixel_array)
            k+=1
            firstforsid.append(k)
        for j in range(len(h)):
            uid=ds.ExposureSequence[j]
            var_i.append(uid["GantryAngle"].value)
        try:
            npkV.append((len(h)+npkV[len(npkV)-1]))
        except:
            npkV.append(len(h))
        sid.append(ds.RTImageSID)
        RefBeamNumber.append(ds.ReferencedBeamNumber)
    logger.debug(f"End of pkV image extraction")
    return var_i,sid,npkV,firstforsid,RefBeamNumber
#########################################################################################################
def convert_dcm_to_nii(dcm_folder, nii_path, skip=False, relative_nii_path=None): #mettre skip a True a la fin
    """
    Converts a dicom (.dcm) folder into a single nii (.nii) file.

    input:
    - dcm_folder (str): Path of the folder containing DICOM Files.
    - nii_path (str): Path of the save location for the nii file
    - skip (bool): Allows the conversion to be skipped if the test is true. Default is True.
    - relative_nii_path (str, optional): relative path for logging purposes. Default is None.

    output:
    - None
    """
    logger.debug(f"Start of conversion to .nii")
    # Create output directory if necessary
    os.makedirs(os.path.dirname(nii_path), exist_ok=True)
    nii_path = Path(nii_path)

    # Check if the output file already exists
    if skip and nii_path.exists():
        logger.info(f"Skipped, already converted")
        return  # Do nothing if the file already exists

    else:
        # Read all DICOM files in the folder
        dcm_files = sorted(Path(dcm_folder).glob('*.dcm'))
        if not dcm_files:
            logger.warning(f"No DICOM files in the folder: {dcm_folder}")
            return

        # Read DICOM images and combine them into a single volumetric image
        reader = sitk.ImageSeriesReader()
        L=os.listdir(dcm_folder)
        dicom_names=[]
        for i in L:
            dicom_names.append(dcm_folder+'/'+i)
        reader.SetFileNames(dicom_names)
        reader.SetOutputPixelType(sitk.sitkInt16)
        image = reader.Execute()
        sitk.WriteImage(image, str(nii_path))
        if relative_nii_path:
            logger.debug(f"Converted {relative_nii_path}")
        else:
            logger.debug(f"Converted {nii_path}")
        logger.debug(f"End of conversion to .nii")

#########################################################################################################################################
def command_iteration(method):
    """ Callback invoked when the optimization has an iteration. """
    print(
        f"{method.GetOptimizerIteration():3} "
        + f"= {method.GetMetricValue():10.5f} "
        + f": {method.GetOptimizerPosition()}"
    )

#########################################################################################################################################
def extract_info_pkV(path):
    """
    Description: takes as input the path of the folder containing the pkV
    returns the information related to the spacing, the dimension of the pkV images, and those necessary for creating the report.
    
    input: path(str)
    output: spacingx(float), spacingy(float), ds.Rows(int), ds.Columns(int), patient_ID(str), patient_Name(str), Aquisition_Date(int)
    
    """
    L=os.listdir(path)
    spacingx=[]
    spacingy=[]
    for i in L:
        ds = dcmread(path+"/"+i)
        w=float(ds.ImagePlanePixelSpacing[0])*(ds.Rows/256)
        h=float(ds.ImagePlanePixelSpacing[1])*(ds.Columns/256)
        spacingx.append(h)
        spacingy.append(w)
    patient_ID=ds.PatientID
    patient_Name=ds.PatientName
    Aquisition_Date=ds.AcquisitionDate
    return spacingx,spacingy,ds.Rows,ds.Columns,patient_ID,patient_Name,Aquisition_Date
#########################################################################################################################################
def extract_info_RTP(path,RefBeamNumber):
    """
    Description: takes as input the path of the folder containing the RTPlan
    returns the information necessary for creating the report.
    
    input: path(str)
    output: RTPLANLABEL(str)
    
    """
    L=os.listdir(path)
    ds=dcmread(path+"/"+L[0])
    RTPLANLABEL=ds.RTPlanLabel
    ds=ds.BeamSequence
    BeamNameRTP=[]
    BeamNumberRTP=[]
    for i in range(len(ds)):
        BeamNumberRTP.append(ds[i].BeamNumber)
    for i in RefBeamNumber:
        BeamNameRTP.append(ds[BeamNumberRTP.index(i)].BeamName)
    return RTPLANLABEL,BeamNameRTP
#########################################################################################################################################
def erase_file(path):
    """
    Description: Erases the content of the folder located at path (only works if the folder does not contain another folder).
        
    input: path(str)
    output: None
    
    """
    if os.listdir(path)==[]:
        # logger.debug(f"The folder is empty")
        return
    for file in os.listdir(path):
        os.remove(path+"/"+file)
        # logger.debug(f"The folder has been successfully emptied")
#########################################################################################################################################
def create_directories(path):
    """
    Description: Creates the folder located at path as well as all the folders necessary to reach it.
        
    input: path(str)
    output: None
    
    """
    if os.access(path, os.F_OK)==False:
        os.makedirs(path)
    return
# #########################################################################################################################################
def reconstruct_ct(gantry_angle_pkv,sid,spacingx,spacingy,Rows,Columns,firstforsid,input_path, output_path, relative_output_path=None, progress=None) -> None:
    """
    Description:
    Generates DRRs using the kV images as a function of the rotation angle and saves them as tiff files
    
    
    input: gantry_angle_pkv(list), sid(list), spacingx(list), spacingy(list), Rows(int), Columns(int), firstforsid(list),
           input_path(str), output_path(str), relative_output_path=None

    output: None
    """
    logger.debug(f"Start of reconstruction")
    # Create output directory if necessary
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Check if output files already exist
    base, ext = os.path.splitext(output_path)
    # Read the input CT image
    convert_dcm_to_nii(input_path,output_path+"/CT_isocal.nii")
    # Initialize the DRR module for generating synthetic X-rays
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    subject = read(
        volume=path_pCT, # Path to your CT data
        orientation='AP', # Specify the view orientation (AP, PA, etc.)
        bone_attenuation_multiplier=bam, # Optional: Adjust bone contrast
        center_volume=True,
        ) #https://github.com/eigenvivek/DiffDRR/discussions/336
    l=0
    N = len(gantry_angle_pkv)
    for i in range(N):
        if i in firstforsid:
            l+=1
        drr = DRR(
            subject,     # An object storing the CT volume, origin, and voxel spacing
            sdd=sid[l],  # Source-to-detector distance (i.e., focal length)  to be modified to match the case of multiple pkV
            height=256,  # Image height (if width is not provided, the generated DRR is square)
            delx=spacingx[l],    # Pixel spacing (in mm) 
            dely=spacingy[l],
            width =256,# Width of the rendered DRR (default to height)
        ).to(device)
        # Set the camera pose with rotations (yaw, pitch, roll) and translations (x, y, z)
        translations = torch.tensor([[0.0,1000,0.0 ]], device=device)
        rotations = torch.tensor([[(2*torch.pi/360)*gantry_angle_pkv[i],0,0]], device=device)
        # 📸 Also note that DiffDRR can take many representations of SO(3) 📸
        # For example, quaternions, rotation matrix, axis-angle, etc.
        img = drr(rotations, translations, parameterization="euler_angles", convention="ZXY")
        plot_drr(img, ticks=False)
        plt.gca().set_axis_off()
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, 
                    hspace = 0, wspace = 0)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        imgdata = BytesIO()
        plt.savefig(imgdata, bbox_inches='tight',pad_inches = 0)
        plt.close()
        im = Image.open(imgdata)
        im = im.resize((Columns,Rows))
        im= im.convert("I;16").save(output_path+"/tiff_isocal/im_isocal"+str(i)+".tif")
        
        # At the end of iteration i:
        if progress is not None:
            progress.step(1, msg=f"Generating DRRs ({i+1}/{N})")
    # Log the relative output path if provided
    if relative_output_path:
        logger.debug(f"Reconstructed {relative_output_path}")
    else:
        logger.debug(f"Reconstructed {output_path}")
    return
# #########################################################################################################################################
def extract_result(tfm_path):
    """
    Description: extracts the data related to the registration
        
    input: recap_path(str)
    output: (pixelvaluex(float), pixelvaluey(float)) (tuple)
    
    """
    tx = sitk.ReadTransform(tfm_path)

    # Simple case: TranslationTransform
    if tx.GetName() == "TranslationTransform":
        dx, dy = tx.GetParameters()  # (dx, dy)
        return [float(dx), float(dy)]

    # Composite case (depending on pipeline/versions)
    if isinstance(tx, sitk.CompositeTransform):
        # Look for the first translation
        for k in range(tx.GetNumberOfTransforms()):
            t = tx.GetNthTransform(k)
            if t.GetName() == "TranslationTransform":
                dx, dy = t.GetParameters()
                return [float(dx), float(dy)]
        # Fallback: parameters of the first transform
        params = tx.GetNthTransform(0).GetParameters()
        return [float(params[0]), float(params[1])]

    # Generic fallback: take the first 2 parameters
    params = tx.GetParameters()
    if len(params) < 2:
        raise ValueError(f"Unexpected transform in {tfm_path}: {tx.GetName()}, params={params}")
    return [float(params[0]), float(params[1])]

# #########################################################################################################################################
def report(output_path,npkV,spacingx,spacingy,GantryAngle,patient_ID,patient_Name,Aquisition_Date,RTPLabel,BeamName):
    """
    Description: creates a registration report in the folder where the program is located
        
    input: output_path(str), npkV(list), spacingx(float), spacingy(float), GantryAngle(list),
           patient_ID(str), patient_Name(str), Aquisition_Date(str), RTPLabel(str), BeamName(list)
    output: None
    
    """
    logger.debug(f"Start of report writing")
    # Extract registration info
    Xrecal=[]
    Yrecal=[]
    for r in range(len(os.listdir(output_path+"/recap"))):
       R=extract_result(output_path+"/recap/recap"+str(r)+".tfm")
       Xrecal.append(R[0])
       Yrecal.append(R[1])
       Xmm=[i*spacingx for i in Xrecal]
       Ymm=[i*spacingy for i in Yrecal]
       
       Vect=[]
       for i in range(len(Xmm)):
            Vect.append(np.sqrt(Xmm[i]**2+Ymm[i]**2))
    moyVect=sum(Vect)/len(Vect)
    moyX= sum(Xmm)/len(Xmm)
    moyabsX=sum(np.abs(np.array(Xmm)))/len(Xmm)
    moyY=sum(Ymm)/len(Ymm)
    moyabsY=sum(np.abs(np.array(Ymm)))/len(Ymm)
    etx,ety,etxa,etya,etn=0,0,0,0,0
    for s in range(len(Xmm)):
        etx+=(Xmm[s]-moyX)**2
        ety+=(Ymm[s]-moyY)**2
        etxa+=(np.abs(Xmm[s])-moyabsX)**2
        etya+=(np.abs(Ymm[s])-moyabsY)**2
        etn+=(Vect[s]-moyVect)**2
    etx=np.sqrt(etx/len(Xmm))
    etxa=np.sqrt(etxa/len(Xmm))
    ety=np.sqrt(ety/len(Ymm))
    etya=np.sqrt(etya/len(Ymm))
    etn=np.sqrt(etn/len(Vect))
    # create a Canvas object with a filename
    pdf_path = os.path.join(output_path, "registration_report.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter  # A4 pagesize
    #Create centered underlined title
    # First page - patient information
    c.setFont("Helvetica",18)
    c.drawCentredString(width/2,height-50, "Patient Information")
    
    c.line(width/2-132, height-55,width/2+132, height-55)
    data=[["Patient ID",patient_ID],
          ["Last Name",str(patient_Name)[0:str(patient_Name).find('_')]],
          ["First Name",str(patient_Name)[str(patient_Name).find('_')+1:]],
          ["Plan Name",RTPLabel],
          ["Treatment Date",str(Aquisition_Date[6:8])+" / "+str(Aquisition_Date[4:6])+" / "+str(Aquisition_Date[0:4]),]]
    t=Table(data,colWidths=width/4,rowHeights=height/12)
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.25, colors.black),('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    t.wrapOn(c,width/3,height*2/3)
    t.drawOn(c, width/4, height/3)
    #create a new page with a Centred underlined title and the 
    # Second page - general data on registration
    # Data and image of the registration
    c.showPage()
    c.setFont("Helvetica",18)
    c.drawCentredString(width/2,height-50, "Summary")
    c.line(width/2-35, height-55,width/2+35, height-55)
    data=[["Maximum absolute shift along x",str("%.2f" % max([abs(x)for x in Xmm]))+" mm"],
          ["Maximum absolute shift along y",str("%.2f" % max([abs(y)for y in Ymm]))+" mm"],
          ["Norm of the maximum shift vector ",str("%.2f" %max(Vect))+" mm"],
          ["Average shift along x +/- standard deviation",str("%.2f" % moyX)+" mm +/- "+str("%.2f" % etx)+" mm"],
          ["Average absolute shift along x +/- standard deviation",str("%.2f" % moyabsX)+" mm +/- "+str("%.2f" % etxa)+" mm"],
          ["Average shift along y +/- standard deviation",str("%.2f" % moyY)+" mm +/- "+str("%.2f" % ety)+" mm"],
          ["Average absolute shift along y +/- standard deviation",str("%.2f" % moyabsY)+" mm +/- "+str("%.2f" % etya)+" mm"],
          ["Average norm of the shift vector +/- standard deviation",str("%.2f" % moyVect)+" mm +/- "+str("%.2f" % etn)+" mm"]]
    t=Table(data,colWidths=width*0.45,rowHeights=height*0.04)
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.25, colors.black),('ALIGN',(-1,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    t.wrapOn(c,width/3,height*2/3)
    t.drawOn(c, (width-width*0.90)/2, height*0.6)
    
    c.drawCentredString(width/2,height*0.6-30,"Shift along x and y as a function of acquisition angle")
    
    # Spider graph
    h=(height/40)+10
    for i in range(len(npkV)):
        
        spidercdata1={'group':["X","Y"]}
        spidercdata2={}
        if i!=0:
            for j in range(npkV[i-1],npkV[i]) :
                spidercdata2[int(GantryAngle[j])]=[Xmm[j],Ymm[j]]
        else:
            for j in range(0,npkV[i]) :
                spidercdata2[int(GantryAngle[j])]=[Xmm[j],Ymm[j]]
        spidercdata2=dict(sorted(spidercdata2.items()))
        spidercdata={**spidercdata1,**spidercdata2}
        df=pd.DataFrame(spidercdata) 
        
        # ------- PART 1: Create background
         
        # Number of variables
        categories=list(df)[1:]
        N = len(categories)
        # What will be the angle of each axis in the plot? (we divide the plot / number of variables)
        angles=[0.0]
        if N !=1:
            for n in range(0,N-2):
                angles.append(float(angles[-1]+(int(categories[n+1])-int(categories[n]))/180*np.pi))
            angles.append(float((((int(categories[N-1])-int(categories[0]))))/180*np.pi))
        # Initialize the spider plot
        ax = plt.subplot( polar=True)
         
        # If you want the first axis to be on top:
        ax.set_theta_offset((np.pi/2-(categories[0]*np.pi/180)))
        ax.set_theta_direction(-1)
         
        # Draw one axis per variable + add labels
        plt.xticks(angles, categories)
         
        # Draw ylabels
        ax.set_rlabel_position(0)
        plt.yticks( color="grey", size=7)
        # Add legend
        fc=["b","r"]
        for n in range(0,2):
            values=df.loc[n].drop('group').values.flatten().tolist()
            values += values[:0]
            if n==1:
                ax.plot(angles, values,"o", linewidth=1, linestyle='solid', label=str(spidercdata["group"][n])+" (mm)   ――  Acquisition angle (in °)", ms=2)
            else:
                ax.plot(angles, values,"o", linewidth=1, linestyle='solid', label=str(spidercdata["group"][n])+" (mm)", ms=2)
            ax.fill(angles, values,facecolor=fc[n], alpha=0.15, label='_nolegend_')
        ax.tick_params(axis='x',labelsize=8,direction="out")
        ax.set_title("Shift for file: "+BeamName[i])  # Add a title to the Axes.
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.056),fancybox=True, shadow=False, ncol=5)
        imgdata = BytesIO()
        plt.savefig(imgdata, dpi=300)
        #plt.savefig(f"graph{i}.png", dpi=300)
        Image = ImageReader(imgdata)
        c.drawImage(Image,0,h, width,height/2)
        plt.close()
        if h<=height/20+10:
            h=(height/2)-10
            c.showPage()
            pagejump=True
        else:
            h=height/40
            pagejump=False
    if pagejump==False:
        c.showPage()
        
    # Graph of shift along x and y as a function of angle.
    for i in range(len(npkV)):
        fig, ax = plt.subplots()
        c.setFont("Helvetica",18)
        c.drawCentredString(width/2,height-50, "Data concerning the pkV file: "+BeamName[i])
        if i!=0:
            xn=list(str("%.2f" % j) for j in GantryAngle[npkV[i-1]:npkV[i]])
            yn=Xmm[npkV[i-1]:npkV[i]]
        else:
            xn=list(str("%.2f" % j) for j in GantryAngle[0:npkV[i]])
            yn=Xmm[0:npkV[i]]
        ax.plot(xn, yn,'-o',alpha=1)
        if len(xn)>=8:
            ax.xaxis.set_major_locator(plt.MaxNLocator(int(len(xn)/2)))
        ax.tick_params(axis='x',labelrotation = 45,right=True,labelsize=8)
        plt.title("Shift along x as a function of acquisition angle")
        plt.xlabel("Acquisition angle (in °)")
        plt.ylabel('Shift along x (in mm)')
        plt.subplots_adjust(top=0.925, 
                    bottom=0.20)
        ax.grid(True)
        imgdata = BytesIO()
        fig.savefig(imgdata, dpi=300)
        Image = ImageReader(imgdata)
        c.drawImage(Image,0,height*0.51, width,height*0.42)
        plt.close()
        
        if i!=0:
            xn=list(str("%.2f" % j) for j in GantryAngle[npkV[i-1]:npkV[i]])
            yn=Ymm[npkV[i-1]:npkV[i]]
        else:
            xn=list(str("%.2f" % j) for j in GantryAngle[0:npkV[i]])
            yn=Ymm[0:npkV[i]]
        fig, ax = plt.subplots()
        ax.plot(xn, yn,'-o',alpha=1)
        if len(xn)>=8:
            ax.xaxis.set_major_locator(plt.MaxNLocator(int(len(xn)/2)))
        ax.tick_params(axis='x',labelrotation = 45,right=True,labelsize=8)
        plt.title("Shift along y as a function of acquisition angle")
        plt.xlabel("Acquisition angle (in °)")
        plt.ylabel('Shift along y (in mm)')
        plt.subplots_adjust(top=0.925, 
                    bottom=0.20)
        ax.grid(True)
        imgdata = BytesIO()
        fig.savefig(imgdata, dpi=300)
        Image = ImageReader(imgdata)
        c.drawImage(Image,0,height*0.05, width,height*0.42)
        plt.close()
        c.showPage()

#   # This commented part is optional. It may contain bugs not fixed with the new versions of the program        
#   # Another possibility, plot all arcs on the same
#   # Test valid only for 2 pkV for now but functional
#     x0=[]
#     fig0,a0 = plt.subplots()
#     fig, ax = plt.subplots()
#     fig2, ay = plt.subplots()
#     # ########################################################################################################################
#     def sort_arcs(x0,L1,L2,i):
#         L3=L1+L2
#         L3.sort()
#         sto=[]
#         #take the lowest or the highest depending on the direction.
#         if (L2[0]>L2[1] and L1[0]>L1[0]) or  (L2[0]<L2[1] and L1[0]<L1[0]):
#             L2.reverse()
#         if L1[0]>L1[1] and L1[0]<L2[0]:
#             for i in L3:
#                 if i<=L1[0]:
#                     x0.append(i)
#                 else:
#                     sto.append(i)
#         elif L1[0]<L1[1] and L1[0]>L2[0]:
#             for i in L3:
#                 if i>=L1[0]:
#                     x0.append(i)
#                 else:
#                     sto.append(i)
#         elif L2[0]>L2[1] and L1[0]<L2[0]:
#             for i in L3:
#                 if i<=L2[0]:
#                     x0.append(i)
#                 else:
#                     sto.append(i)
#         elif L2[0]<L2[1] and L1[0]>L2[0]:
#             for i in L3:
#                 if i>=L2[0]:
#                     x0.append(i)
#                 else:
#                     sto.append(i) 
#         for j in sto:
#             x0.append(j)
#         return(x0)
#     L1=list(float(i) for i in GantryAngle[0:npkV[0]])
# # #################################### creation of the artificial x-axis.
#     for i in range(1,len(npkV)):
#         L2=list(float(j)for j in GantryAngle[npkV[i-1]:npkV[i]])
#         L1=sort_arcs(x0, L1, L2,i)
#         x0=[]
#     if len(npkV)==1:
#         x0=GantryAngle
#     x0=list(str("%.2f" % j) for j in L1)

#     # ########################################################################################################################
#     for i in range(len(npkV)):
#           c.setFont("Helvetica",18)
#           c.drawCentredString(width/2,height-50, "pkV Data ")
#           if i!=0:
#               xn=list(str("%.2f" % j) for j in GantryAngle[npkV[i-1]:npkV[i]])
#               ynx=Xmm[npkV[i-1]:npkV[i]]
#               yny=Ymm[npkV[i-1]:npkV[i]]
#           else:
#               xn=list(str("%.2f" % j) for j in GantryAngle[0:npkV[i]])
#               ynx=Xmm[0:npkV[i]]
#               yny=Ymm[0:npkV[i]]
#           ax.plot(x0,Xmm[:len(GantryAngle)],color="blue", alpha=0, label='_nolegend_')
#           ax.plot(xn, ynx,alpha=0.8,color=np.random.rand(3,),label=(str(os.listdir(path_pkV)[i])[0:3]+".."+str(os.listdir(path_pkV)[i])[20:23]))
#           ay.plot(x0,Ymm,color="blue", alpha=0, label='_nolegend_')
#           ay.plot(xn, yny,alpha=0.8,color=np.random.rand(3,),label=(str(os.listdir(path_pkV)[i])[0:3]+".."+str(os.listdir(path_pkV)[i])[20:23]))
#     ax.set_title("Shift along x as a function of acquisition angle")
#     ax.set_xlabel("observation angle (in °)")
#     ax.set_ylabel('shift along x (in mm)')
#     ax.xaxis.set_major_locator(plt.MaxNLocator(int(len(xn)/2)))
#     ax.tick_params(axis='x',labelrotation = 45,right=True,labelsize=8)
#     ax.grid(False)
#     ax.legend(loc='upper center', bbox_to_anchor=(1, 0.5), shadow=False, ncol=1)
#     imgdata = BytesIO()
#     fig.savefig(imgdata)
#     Image = ImageReader(imgdata)
#     c.drawImage(Image,0,height*0.51, width,height*0.42)
#     plt.close(fig)
   
#     ay.set_title("Shift along y as a function of acquisition angle")
#     ay.set_xlabel("observation angle (in °)")
#     ay.set_ylabel('Shift along y (in mm)')
#     ay.xaxis.set_major_locator(plt.MaxNLocator(int(len(xn)/2)))
#     ay.tick_params(axis='x',labelrotation = 45,right=True,labelsize=8)
#     ay.grid(False)
#     box = ay.get_position()
#     ay.set_position([box.x0, box.y0, box.width * 0.7, box.height])
#     ay.legend(loc='center left', bbox_to_anchor=(1,0.5))
#     imgdata = BytesIO()
#     fig2.savefig(imgdata)
#     Image = ImageReader(imgdata)
#     c.drawImage(Image,0,height*0.05, width,height*0.42)
#     plt.close(fig2)
#     c.showPage()


    # Test end

    # # Initial function 
    # fig, ax = plt.subplots()
    # fig2, ay = plt.subplots()
    # for i in range(len(npkV)):
    #       c.setFont("Helvetica",18)
    #       c.drawCentredString(width/2,height-50, "pkV Data ")
    #       if i!=0:
    #           xn=list(str("%.2f" % j) for j in GantryAngle[npkV[i-1]:npkV[i]])
    #           ynx=Xmm[npkV[i-1]:npkV[i]]
    #           yny=Ymm[npkV[i-1]:npkV[i]]
    #       else:
    #           xn=list(str("%.2f" % j) for j in GantryAngle[0:npkV[i]])
    #           ynx=Xmm[0:npkV[i]]
    #           yny=Ymm[0:npkV[i]]
    #       ax.plot(xn, ynx,alpha=0.8,color=np.random.rand(3,),label=str(os.listdir(path_pkV)[i])[0:23])
    #       ay.plot(xn, yny,alpha=0.8,color=np.random.rand(3,),label=str(os.listdir(path_pkV)[i])[0:23])
    # ax.set_title("Shift along x as a function of acquisition angle")
    # ax.set_xlabel("observation angle (in °)")
    # ax.set_ylabel('shift along x (in mm)')
    # ax.xaxis.set_major_locator(plt.MaxNLocator(int(len(xn)/2)))
    # ax.tick_params(axis='x',labelrotation = 45,right=True,labelsize=8)
    # ax.grid(False)
    # ax.legend(loc='upper center', bbox_to_anchor=(1, 0.5), shadow=False, ncol=1)
    # imgdata = BytesIO()
    # fig.savefig(imgdata)
    # Image = ImageReader(imgdata)
    # c.drawImage(Image,0,height*0.51, width,height*0.42)
    # plt.close(fig)
    
    # ay.set_title("Shift along y as a function of acquisition angle")
    # ay.set_xlabel("observation angle (in °)")
    # ay.set_ylabel('Shift along y (in mm)')
    # ay.xaxis.set_major_locator(plt.MaxNLocator(int(len(xn)/2)))
    # ay.tick_params(axis='x',labelrotation = 45,right=True,labelsize=8)
    # ay.grid(False)
    # box = ay.get_position()
    # ay.set_position([box.x0, box.y0, box.width * 0.7, box.height])
    # ay.legend(loc='center left', bbox_to_anchor=(1,0.5))
    # imgdata = BytesIO()
    # fig2.savefig(imgdata)
    # Image = ImageReader(imgdata)
    # c.drawImage(Image,0,height*0.05, width,height*0.42)
    # plt.close(fig2)
    # c.showPage()
    
## Replace the above with the simultaneous plot function if needed.    
    
    c.setFont("Helvetica",18)
    c.drawCentredString(width/2,height-50, "Registration Report")
    c.line((width/2)-82, height-55,width/2+82, height-55)
    c.setFont("Helvetica",12)
    c.drawString(25, height-150,"Spacing x: "+str("%.2f" % spacingx)+" (mm/pixel)")
    c.drawString(25, height-165,"Spacing y: "+str("%.2f" % spacingy)+" (mm/pixel)")
    try:
        c.drawString(25, height-180,"Crop: "+str("%.2f" % (crop_values[0]*sx))+" , "+str("%.2f" % (crop_values[1]*sy))+" (cm)")
    except:
        c.drawString(25, height-180,"Crop: "+str(crop_values))
    c.drawString(25, height-195,"Bone attenuation multiplier: "+str(bam))
    h=height-250
    sp=height*0.29
    for i in range(len(GantryAngle)):
        c.drawString(25,h-(i*sp),"Angle: "+str("%.2f" % GantryAngle[i])+" inst "+str(i+1))
        c.drawImage(output_path+"/imgreport/im_registered"+str(i)+"checkerboard.png", width=150, height=150,x=25,y=h-(i*sp)-160)
        c.drawImage(output_path+"/imgreport/im_registered"+str(i)+".png", width=150, height=150,x=420,y=h-(i*sp)-160)
        c.drawString(260,h-(i*sp)-20,"Shift in pixels")
        c.drawString(200,h-(i*sp)-40,"Shift along x: "+str("%.2f" % Xrecal[i]))
        c.drawString(200,h-(i*sp)-65,"Shift along y: "+str("%.2f" % Yrecal[i]))
        c.drawString(260,h-(i*sp)-110,"Shift in mm ")
        c.drawString(200,h-(i*sp)-130,"Shift along x: "+str("%.2f" % Xmm[i]))
        c.drawString(200,h-(i*sp)-155,"Shift along y: "+str("%.2f" % Ymm[i]))
        if h-(i*sp)<sp*2:
            h=(height+((i)*sp))+150
            c.showPage() # Close the current page and possibly start on a new page.
    # finish page
    # Construct and save file to .pdf
    c.save()
    logger.debug(f"End of report writing pdf")
    # #########################################################################################################################################

    logger.debug(f"Start of report writing csv")
    categories=["BeamName","Gantry Angle","Shift along X (mm)","Shift along Y (mm)"]
    csv_path = os.path.join(output_path, "registration_report.csv")
    with open(csv_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=categories,delimiter=';') # Create a writer object
        writer.writeheader()
        for i in range(len(npkV)):
            if i!=0:
                for j in range(npkV[i-1],npkV[i]):
                    writer.writerow({"BeamName":str(BeamName[i]),"Gantry Angle":str(GantryAngle[j]),"Shift along X (mm)":str(Xmm[j]),"Shift along Y (mm)":str(Ymm[j])})
            else:
                for j in range(0,npkV[i]):
                    writer.writerow({"BeamName":str(BeamName[i]),"Gantry Angle":str(GantryAngle[j]),"Shift along X (mm)":str(Xmm[j]),"Shift along Y (mm)":str(Ymm[j])})
                
# #########################################################################################################################################
def crop_choice(Rows,Columns):
    """
    Description: Creates a choice window
    If the answer is yes, calls the 'new_window' function
    If the answer is no, closes the window.
        
    input: Rows(int), Columns(int)
    output: None
    
    """
    # ############################
    def new_window():
        """
        Description: Closes the choice window and opens the crop configuration window
            
        input: None
        output: None
        
        """
        root.destroy()
        Def_Val_crop()
    # ############################
    global row, column, crop_values
    row=Rows
    column= Columns
    crop_values=None
    root = tk.Tk()
    root.geometry('400x110')
    root.title("Crop Choice")
    frm = ttk.Frame(root, padding=10,height=400,width=100 )
    frm.pack(anchor="center",expand=True)
    ttk.Label(frm, text="Do you want to define a crop area?").pack(ipady=10,anchor="n")
    ttk.Button(frm, text="No", command=root.destroy).pack(side="left",anchor="s")
    ttk.Button(frm, text="Yes", command=new_window).pack(side="right",anchor="s")
    root.mainloop()
    return
# #########################################################################################################################################
def Def_Val_crop():
    """
    Description: Creates a crop configuration window allowing the crop dimensions to be entered.
    If the 'Use these values' button is pressed, the data is sent to the program.
    If the 'Do not define crop' button is pressed, closes the window without taking the entries into account.
    If the window is closed, uses the Default value (None)
    
    input: None
    output: None
    
    """
    subw=tk.Tk()
    subw.title("Crop Configuration")
    subw.geometry('410x170')
    frm = ttk.Frame(subw, padding=10,height=410,width=270 )
    frm.pack(anchor="center",expand=True)
    ttk.Label(frm, text="Enter crop values in cm").pack(side="top")
    sfrm1=ttk.Frame(frm, padding=10,height=200,width=200 )
    sfrm1.pack()
    sfrm2=ttk.Frame(frm, padding=10,height=200,width=200 )
    sfrm2.pack()
    tk.Label(sfrm1, text = 'Crop width:').pack(side="left",anchor="center")
    entryx1 =tk.Entry(sfrm1)
    entryx1.insert(0,str("%.2f" % (column*sx)) ) #Default Value
    entryx1.pack(side="left",anchor="center")
    tk.Label(sfrm2, text = 'Crop height:').pack(side="left",anchor="center")
    entryy1 =tk.Entry(sfrm2)
    entryy1.insert(0, str("%.2f" % (row*sy))) #Default Value
    entryy1.pack(side="left",anchor="center")
    # ############################
    def setvalue():
        """
        Description:
            makes the crop_values variable global and assigns it a tuple.
            then closes the window
        input: None
        output: None
        """
        global crop_values
        crop_values=(int(float(entryx1.get())/sx),int(float(entryy1.get())/sy))
        subw.destroy()
    # ############################
    ttk.Button(frm, text="Do not define crop", command=subw.destroy).pack(side="left")
    ttk.Button(frm, text="Use these values", command=setvalue).pack(side="right")
    subw.focus()
    subw.mainloop()
    return
# #########################################################################################################################################
def Def_Val_Bone():
    """
    Description: Creates a configuration window for the diffDRR bone_attenuation_multiplier parameter
    which modifies the contrast.
    
    If the 'Use these values' button is pressed, the data is sent to the program.
    If the 'Do not define crop' button is pressed, closes the window without taking the entries into account.
    If the window is closed, uses the Default values (3.0)
    
    input: None
    output: None
    
    """
    subw=tk.Tk()
    subw.title("Configuration of the bone_attenuation_multiplier parameter")
    subw.geometry('410x170')
    global bam
    bam=3.0
    frm = ttk.Frame(subw, padding=10,height=410,width=270 )
    frm.pack(anchor="center",expand=True)
    ttk.Label(frm, text="Enter the value of the bone_attenuation_multiplier parameter").pack(side="top")
    sfrm1=ttk.Frame(frm, padding=10,height=200,width=200 )
    sfrm1.pack()
    entryx1 =tk.Entry(sfrm1)
    entryx1.insert(0,str("%.2f" % (3.0)) ) #Default Value
    entryx1.pack(side="left",anchor="center")
    def setvalue():
        global bam
        bam=float(entryx1.get())
        subw.destroy()
    ttk.Button(frm, text="Default value", command=subw.destroy).pack(side="left")
    ttk.Button(frm, text="Set this value", command=setvalue).pack(side="right")
    subw.focus()
    subw.mainloop()
    return

# #########################################################################################################################################

# ---------------------------------------------------------------------------
# TO DISPLAY A PROGRESS BAR
# ---------------------------------------------------------------------------
class ProgressGUI:
    def __init__(self, total:int, title:str="Processing", width_px:int=420):
        self.total = max(1, int(total))
        self.count = 0
        self.start_time = time.time()

        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)

        frm = ttk.Frame(self.root, padding=12)
        frm.grid(sticky="nsew")

        self.lbl = ttk.Label(frm, text=title, anchor="w")
        self.lbl.grid(row=0, column=0, sticky="we", pady=(0,8))

        self.pb = ttk.Progressbar(frm, orient="horizontal",
                                  mode="determinate", length=width_px)
        self.pb["maximum"] = self.total
        self.pb["value"] = 0
        self.pb.grid(row=1, column=0, sticky="we")

        self.info = ttk.Label(frm, text="0% — ETA: …", anchor="w")
        self.info.grid(row=2, column=0, sticky="we", pady=(8,0))

        # Make the window always on top (optional)
        self.root.attributes("-topmost", True)
        self.root.update()

    def _eta_text(self):
        elapsed = time.time() - self.start_time
        rate = self.count / elapsed if elapsed > 0 else 0
        rem = (self.total - self.count) / rate if rate > 0 else 0
        def fmt(t):  # small mm:ss formatter
            m, s = divmod(int(t), 60)
            return f"{m:02d}:{s:02d}"
        return f"{fmt(elapsed)} elapsed | ETA {fmt(rem)}"

    def step(self, n:int=1, msg:str=None):
        self.count = min(self.total, self.count + n)
        self.pb["value"] = self.count
        pct = int(100 * self.count / self.total)
        if msg:
            self.lbl.config(text=msg)
        self.info.config(text=f"{pct}% — {self._eta_text()}")
        self.root.update_idletasks()
        self.root.update()

    def set_total(self, total:int):
        self.total = max(1, int(total))
        self.pb["maximum"] = self.total
        self.root.update_idletasks()
        self.root.update()

    def close(self):
        try:
            self.root.destroy()
        except:
            pass
    
# #########################################################################################################################################  

def main(reuse_drr=False):
    """
    Description: Runs the checks,
    generates the DRRs from the dicoms,
    reads the pkV and the RTP to extract the essential information,
    performs the registration of the generated DRRs onto the pkV images,
    generates checkerboard images and registered images for each angle before generating a report.
        
    input: None
    output: None
    
    """

   
    
    # Extraction of angles 
    logger.debug(f"Start of main")
    logger.debug(f"Create access paths if necessary ")
    if not os.path.exists("DICOM Files/01pCT"):
        create_directories("DICOM Files/01pCT")
    if not os.path.exists("DICOM Files/02RTSTRUCT"):
        create_directories("DICOM Files/02RTSTRUCT")
    if not os.path.exists("DICOM Files/03RTPLAN"):
        create_directories("DICOM Files/03RTPLAN")
    if not os.path.exists("DICOM Files/04pkV"):
        create_directories("DICOM Files/04pkV")
    logger.debug(f"Creation completed")
    global path_pCT,path_RTS,path_RTP,path_pkV
    path_pCT="DICOM Files/01pCT"
    path_RTS="DICOM Files/02RTSTRUCT"
    path_RTP="DICOM Files/03RTPLAN"
    path_pkV="DICOM Files/04pkV"
    # output_path configurable via global variable (set in process_dicom_folders)
    global output_path
    try:
        output_path
    except NameError:
        output_path = "test/mhatest"
    create_directories(output_path+"/imgreport")
    create_directories(output_path+"/registration")
    create_directories(output_path+"/tiff_isocal")
    create_directories(output_path+"/recap")
    create_directories(output_path+"/pkslice")
    create_directories(output_path+"/graph")
    erase_file(output_path+"/recap")
    erase_file(output_path+"/registration")
    erase_file(output_path+"/imgreport")
    # Do NOT delete these if reusing already produced DRR/kV
    if not reuse_drr:
        erase_file(output_path+"/pkslice")
        erase_file(output_path+"/tiff_isocal")
        
    # Also save all logs
    log_file = os.path.join(output_path, "execution_log.txt")

    logger.remove()  # remove default handlers
    logger.add(sys.stderr, level="DEBUG")  # console
    logger.add(
        log_file,
        level="DEBUG",
        rotation="10 MB",
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )
    class Tee:
        def __init__(self, *files):
            self.files = files
        def write(self, obj):
            for f in self.files:
                f.write(obj)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
    
    log_f = open(log_file, "a", encoding="utf-8")
    sys.stdout = Tee(sys.stdout, log_f)
    sys.stderr = Tee(sys.stderr, log_f)
        
    if full_check(path_pCT,path_RTP,path_pkV,path_RTS) is True:
        logger.debug(f"End of check")
        gantry_angle_pkv,sid,npkV,firstforsid,RefBeamNumber=extract_angle_pkV(path_pkV,output_path, reuse_drr=reuse_drr)
        input_path=path_pCT
        spacingx,spacingy,Rows,Columns,patient_ID,patient_Name,Aquisition_Date=extract_info_pkV(path_pkV)
        global sx,sy
        sx=spacingx[0]*256/Columns/(sid[0]/1000)
        sy=spacingy[0]*256/Rows/(sid[0]/1000)
        RTPLabel,BeamName=extract_info_RTP(path_RTP,RefBeamNumber)
        #crop_choice(Rows,Columns) #To add if you want to run the analysis with a different crop of 150
        global row, column, crop_values #To remove if you want to run the analysis with a different crop of 150
        row=Rows #idem
        column= Columns #idem
        crop_values=(int(float(150)/sx),int(float(150)/sy)) #idem
        #Def_Val_Bone() #To add if you want to run the analysis with a different crop of 150
        global bam #To remove if you want to run the analysis with a different bam of 3
        bam = 3 #idem
        #logger.debug(f"crop set to:"+str(crop_values))
        
        tiff_files_li = []
        
        if not reuse_drr:
            #progress bar
            pg_drr = ProgressGUI(total=len(gantry_angle_pkv), title="Generating DRRs")
            
            #DRR generation
            reconstruct_ct(gantry_angle_pkv,
                            sid,
                            spacingx,
                            spacingy,
                            Rows,
                            Columns,
                            firstforsid,
                            input_path,
                            output_path,
                            relative_output_path=None,
                            progress=pg_drr)
            tiff_files_li=[]
        
            #close progress bar
            pg_drr.close()
            
            # Check that the required files exist before registration
            missing = []
            for i in range(len(gantry_angle_pkv)):
                f = os.path.join(output_path, "pkslice", f"DRR_isocal_fourni_slice_{i}.tif")
                m = os.path.join(output_path, "tiff_isocal", f"im_isocal{i}.tif")
                if not os.path.exists(f): missing.append(f)
                if not os.path.exists(m): missing.append(m)
            
            if reuse_drr and missing:
                raise RuntimeError("reuse_drr=True but missing files:\n" + "\n".join(missing[:20]))
            
            def to_float01(img):
                x = img.astype(np.float32)
                mn, mx = np.min(x), np.max(x)
                if mx <= mn + 1e-8:
                    return np.zeros_like(x, dtype=np.float32)
                return (x - mn) / (mx - mn)
            
            def float01_to_uint16(x):
                return (np.clip(x, 0, 1) * 65535.0 + 0.5).astype(np.uint16)
            
            def clahe_uint16(img16, clip=2.0, tile=(8,8)):
                x = img16.astype(np.float32)
                x = (x - x.min()) / (x.max() - x.min() + 1e-8)
                x8 = (x * 255).astype(np.uint8)
            
                clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=tile)
                y8 = clahe.apply(x8)
            
                y = y8.astype(np.float32) / 255.0
                return float01_to_uint16(y)
                        
            # Settings
            CLIP_LIMIT_ADAPT = 0.01
            KERNEL_SIZE      = None
            CLAHE_CLIP       = 10.0
            CLAHE_TILE       = (4,4)
                    
            for i in range(len(gantry_angle_pkv)):

                path_kv  = output_path + f"/pkslice/DRR_isocal_fourni_slice_{i}.tif"
                path_drr = output_path + f"/tiff_isocal/im_isocal{i}.tif"
            
                imgkV  = io.imread(path_kv)
                imgdrr = io.imread(path_drr)
            
                # 1) Histogram matching (global)
                kv_matched = match_histograms(imgkV, imgdrr, channel_axis=None)
            
                # 2) Adaptive histogram equalization (skimage)
                kv_eq  = equalize_adapthist(to_float01(kv_matched), kernel_size=KERNEL_SIZE, clip_limit=CLIP_LIMIT_ADAPT)
                drr_eq = equalize_adapthist(to_float01(imgdrr),     kernel_size=KERNEL_SIZE, clip_limit=CLIP_LIMIT_ADAPT)
            
                kv_eq_u16  = float01_to_uint16(kv_eq)
                drr_eq_u16 = float01_to_uint16(drr_eq)
                
                # 3) Light re-matching after adapthist (stabilizes the checkerboard)
                kv_eq_u16 = match_histograms(kv_eq_u16, drr_eq_u16, channel_axis=None).astype(np.uint16)
            
                # 4) Final CLAHE (micro-contrast)
                kv = clahe_uint16(kv_eq_u16, clip=CLAHE_CLIP, tile=CLAHE_TILE)
                drr = clahe_uint16(drr_eq_u16, clip=CLAHE_CLIP, tile=CLAHE_TILE)
            
                io.imsave(path_kv,  kv,  check_contrast=False)
                io.imsave(path_drr, drr, check_contrast=False)
            
            #Crop the images
            if crop_values !=None:
                for i in range(len(gantry_angle_pkv)):
                    
                    # Crop images
                    tiff_files_li.append(output_path+"/tiff_isocal/im_isocal"+str(i)+".tif")
                    im = Image.open(output_path+"/pkslice/DRR_isocal_fourni_slice_"+str(i)+".tif")
                    im=im.crop(((column-crop_values[0])/2,(row-crop_values[1])/2,column-((column-crop_values[0])/2),row-(((row-crop_values[1]))/2)))
                    im = im.resize(size=(crop_values)) 
                    im= im.convert("I;16").save(output_path+"/pkslice/DRR_isocal_fourni_slice_"+str(i)+".tif")
                    
                    im = Image.open(output_path+"/tiff_isocal/im_isocal"+str(i)+".tif")
                    im=im.crop(((column-crop_values[0])/2,(row-crop_values[1])/2,column-((column-crop_values[0])/2),row-(((row-crop_values[1]))/2)))
                    im = im.resize(size=(crop_values)) 
                    im= im.convert("I;16").save(output_path+"/tiff_isocal/im_isocal"+str(i)+".tif")
            else:
                for i in range(len(gantry_angle_pkv)):
                    tiff_files_li.append(output_path+"/tiff_isocal/im_isocal"+str(i)+".tif")
            tifftools.tiff_concat(tiff_files_li, output_path+"/output_isocal.tif", overwrite=True)
        else:
            logger.debug("reuse_drr=True -> skipping reconstruct_ct (DRR already present)")
                 
        logger.debug(f"Start of registration")
    
        def show_popup(img, title="Image"):
            arr = sitk.GetArrayFromImage(img)
        
            plt.figure(figsize=(6,6))
            plt.imshow(arr, cmap="gray")
            plt.title(title)
            plt.axis("off")
            plt.show()
        
        for i in range(len(gantry_angle_pkv)):
            
            # Registration see https://simpleitk.readthedocs.io/en/master/link_ImageRegistrationMethod4_docs.html
            fixed = sitk.ReadImage(output_path+"/pkslice/DRR_isocal_fourni_slice_"+str(i)+".tif", sitk.sitkFloat32)
            moving = sitk.ReadImage(output_path+"/tiff_isocal/im_isocal"+str(i)+".tif", sitk.sitkFloat32)
            
            fixed = sitk.SmoothingRecursiveGaussian(fixed, sigma=1)
            
            # De-comment to see live images while code is running
            # show_popup(fixed,  "Fixed bin")
            # show_popup(moving, "Moving bin")
            
            # ---------- Pass 1 : MS (robuste) ----------
            R1 = sitk.ImageRegistrationMethod()
            R1.SetMetricAsMeanSquares()
            
            # Multi-resolution: very useful to avoid local minima
            R1.SetShrinkFactorsPerLevel([4, 2, 1])
            R1.SetSmoothingSigmasPerLevel([5, 4, 1])
            
            R1.SetOptimizerAsRegularStepGradientDescent(
                learningRate=4.0, minStep=0.0001, numberOfIterations=200,
                relaxationFactor=0.5, gradientMagnitudeTolerance=1e-10
            )
            R1.SetInitialTransform(sitk.TranslationTransform(fixed.GetDimension()))
            R1.SetInterpolator(sitk.sitkLinear)
            
            R1.AddCommand(sitk.sitkIterationEvent, lambda:command_iteration(R1))
            
            outTx = R1.Execute(fixed, moving)
            
            print("Final dx, dy:", outTx.GetParameters())
            print("-------")
            print(outTx)
            print(f"Optimizer stop condition: {R1.GetOptimizerStopConditionDescription()}")
            print(f" Iteration: {R1.GetOptimizerIteration()}")
            print(f" Metric value: {R1.GetMetricValue()}")
        
            sitk.WriteTransform(outTx,output_path+"/recap/recap"+str(i)+".tfm")
        
            resampler = sitk.ResampleImageFilter()
            resampler.SetReferenceImage(fixed)
            resampler.SetInterpolator(sitk.sitkLinear)
            resampler.SetDefaultPixelValue(100)
            resampler.SetTransform(outTx)
        
            out = resampler.Execute(moving)
            simg1 = sitk.Cast(sitk.RescaleIntensity(fixed), sitk.sitkUInt16)
            simg2 = sitk.Cast(sitk.RescaleIntensity(out), sitk.sitkUInt16)
            cimg = sitk.Compose(simg1, simg2, simg1 // 2.0 + simg2 // 2.0)
            dimg=sitk.CheckerBoard(simg1,simg2,[4,4])
            sitk.WriteImage(cimg, str(output_path+"/registration/im_registered"+str(i)+".tif"))
            sitk.WriteImage(dimg, str(output_path+"/registration/im_registered"+str(i)+"checkerboard.tif"))
            
            # --- SITK to NumPy conversion ---
            fixed_np  = sitk.GetArrayFromImage(fixed).astype(np.float32)
            moving_np = sitk.GetArrayFromImage(moving).astype(np.float32)
            
            # --- Normalization 0-255 ---
            fixed_max  = fixed_np.max()
            moving_max = moving_np.max()
            
            if fixed_max == 0 or moving_max == 0:
                raise RuntimeError("Empty image or max==0 before ECC")
            
            fixed_u8  = (fixed_np  / fixed_max  * 255.0).astype(np.uint8)
            moving_u8 = (moving_np / moving_max * 255.0).astype(np.uint8)
            
            warp_matrix = np.eye(2, 3, dtype=np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 5000, 1e-7)
            
            try:
                cc, warp_matrix = cv2.findTransformECC(
                    fixed_u8, moving_u8, warp_matrix,
                    cv2.MOTION_EUCLIDEAN, criteria
                )
                dx, dy = warp_matrix[0,2], warp_matrix[1,2]
                angle = np.arctan2(warp_matrix[1,0], warp_matrix[0,0]) * 180/np.pi
                logger.debug(f"ECC OK i={i} cc={cc:.6f} dx={dx:.2f} dy={dy:.2f} angle={angle:.2f}")
            except cv2.error as e:
                logger.warning(f"ECC FAILED i={i}: {e}")
                # fallback : pas d'ECC, on continue (par ex. angle=0)
                dx = dy = 0.0
                angle = 0.0
            
            print("Rigid ECC dx, dy, angle:", dx, dy, angle)
        tiff_files_li_recal=[]
        
        # Convert checkerboard and recalibrated images from TIFF to PNG
        for i in range(len(gantry_angle_pkv)):
            tiff_files_li_recal.append(output_path+"/registration/im_registered"+str(i)+".tif")
            # Image for the report (in PNG)
            img = io.imread(output_path+"/registration/im_registered"+str(i)+"checkerboard.tif")
            plt.imshow(img,cmap='gray')
            plt.axis('off')
            plt.savefig(output_path+"/imgreport/im_registered"+str(i)+"checkerboard.png", bbox_inches='tight',pad_inches = 0)
            plt.close()
            img = io.imread(output_path+"/registration/im_registered"+str(i)+".tif")
            plt.imshow(img)
            plt.axis('off')
            plt.savefig(output_path+"/imgreport/im_registered"+str(i)+".png", bbox_inches='tight',pad_inches = 0)
            plt.close()
        tifftools.tiff_concat(tiff_files_li_recal, output_path+"/registration/registered_concat.tif", overwrite=True)
        # Generate report
        report(output_path=output_path,
                npkV=npkV,
                spacingx=sx,
                spacingy=sy,
                GantryAngle=gantry_angle_pkv,
                patient_ID=patient_ID,
                patient_Name=patient_Name,
                Aquisition_Date=Aquisition_Date,
                RTPLabel=RTPLabel,BeamName=BeamName)
    logger.debug(f"End of main")
    
def process_dicom_folders(main_folder):
    """
    Finds all folders containing "DICOM Files" in main_folder,
    processes them one by one by renaming them, running main(), then restoring their name
    and moving them into a "done" folder.
    Displays a summary window at the end.
    """
    import shutil
    from tkinter import Tk, ttk, messagebox, Label, Scrollbar, Listbox, END, Button, Toplevel

    # 1. List all folders containing "DICOM Files"
    dicom_folders = [
        d for d in os.listdir(main_folder)
        if os.path.isdir(os.path.join(main_folder, d)) and "DICOM Files" in d
    ]
    dicom_folders.sort()  # For a predictable order

    # Create the "done" folder if it doesn't exist
    done_folder = os.path.join(main_folder, "done")
    os.makedirs(done_folder, exist_ok=True)

    # List to store results
    results = []

    for original_name in dicom_folders:
        original_path = os.path.join(main_folder, original_name)
        temp_path = os.path.join(main_folder, "DICOM Files")

        # 2. Rename the folder to "DICOM Files"
        os.rename(original_path, temp_path)

        try:
            # --- Find all subfolders 04pkV_frX ---
            pkv_parent = os.path.join(temp_path, "04pkV")
            # In your actual tree, you have rather 04pkV_fr1..fr5
            # So we look in temp_path for folders starting with "04pkV_fr"
            pkv_variants = sorted([
                d for d in os.listdir(temp_path)
                if os.path.isdir(os.path.join(temp_path, d)) and d.startswith("04pkV_fr")
            ])

            # Fallback: no 04pkV_frX subfolder, but a plain "04pkV" folder exists
            # (single-fraction case) -> treat it as one variant
            single_pkv = False
            if not pkv_variants and os.path.isdir(pkv_parent):
                pkv_variants = ["04pkV"]
                single_pkv = True

            if not pkv_variants:
                raise RuntimeError("No 04pkV or 04pkV_frX folder found (e.g.: 04pkV_fr1..fr5).")

            patient_status = []

            for pkv_name in pkv_variants:
                pkv_path = os.path.join(temp_path, pkv_name)
                std_pkv_path = os.path.join(temp_path, "04pkV")

                # 1) Temporarily rename 04pkV_frX -> 04pkV
                #    (skip the rename if it's already the plain "04pkV" folder)
                if not single_pkv:
                    os.rename(pkv_path, std_pkv_path)

                try:
                    # 2) Set a unique output_path to avoid overwriting
                    # (global variable read by main() via the mini-patch above)
                    global output_path
                    safe_patient = original_name.replace(" ", "_").replace("/", "_")
                    output_path = os.path.join("test", f"{safe_patient}_{pkv_name}")

                    if __name__ == "__main__":
                        try:
                            #################################### REUSE_DRR
                            ####################################
                            main(reuse_drr=True) 
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            input("Error — press Enter to quit")
                        patient_status.append(f"{pkv_name}: Success")
                except Exception as e:
                    patient_status.append(f"{pkv_name}: Failed ({e})")
                finally:
                    # 3) Restore 04pkV -> 04pkV_frX
                    #    (skip if it's already the plain "04pkV" folder)
                    if not single_pkv:
                        os.rename(std_pkv_path, pkv_path)
            status = " | ".join(patient_status)

        except Exception as e:
            status = f"Failed: {str(e)}"
            print(str(e))

        finally:
            # 4. Restore the original name with "1000_" in front
            new_name = f"{original_name}"
            new_path = os.path.join(main_folder, new_name)
            os.rename(temp_path, new_path)

            # Move the folder to "done" (instead of copying)
            dest_path = os.path.join(done_folder, new_name)
            try:
                shutil.move(new_path, dest_path)
                status += " | Move successful"
            except Exception as e:
                status += f" | Move failed: {str(e)}"

            results.append((original_name, status, new_name))


    # --- Summary window ---
    root = Toplevel()
    root.title("Summary of processed folders")
    root.geometry("700x400")

    # List of results
    lb = Listbox(root, width=85, height=15)
    lb.pack(pady=10, padx=10, fill="both", expand=True)

    # Add results
    for name, status, new_name in results:
        lb.insert(END, f"Folder: {name} → {new_name} | Status: {status}")

    # Close button
    btn_close = Button(root, text="Close", command=root.destroy)
    btn_close.pack(pady=10)

    root.focus_force()
    root.grab_set()
    root.mainloop()
    
if __name__ == "__main__":
    main_folder_path = os.getcwd()
    #print(main_folder_path)# To adapt
    process_dicom_folders(main_folder_path)
    
