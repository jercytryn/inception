% vanishing points and focal length estimation
global GAMMA 
disp('------------------------------------------------------')
clear;
clc;
close;

addpath('Utils');

%set the parameters
Database = 'ECD';% 'YUD': York Urban Database or 'ECD': EurasianCitiesBase
UseLineFromDatabase = 0;%0:use extracted lines, 1:use lines from the database
 
kPlotLines   = true; %flag to decide whether lines are ploted into images
kSaveResults = false;%flag to decide whether the results are stored into disk
ParaList.kMaxNumHyp                = 100;%the max number of hypotheses generated in the ransac procedure.
ParaList.kMinNumHyp                = 40; %the min number of hypotheses generated in the ransac procedure.
ParaList.kAcceptHypothesisThreshold= 0.90;%threshold to accept a hypothesis. When more than 85% inliers are estabilshed by a hypothesis, then stop test the other hypotheses.
ParaList.kRefineMethod             ='Iter'; %the way to refine the estimated vanishing points and classification results:  'Iter' or 'MLE'.
ParaList.kConsistencyMeasure       = 1;%the method to compute the residual of a line with respect to a vanishing point: '1 for CM1' or '2 for CM2'. 
if ParaList.kConsistencyMeasure==1
    ParaList.kInClassResidualThreshold = 0.03;%the threshold to decide whether to accept a line within a class (Xdir, Ydir or Zdir)
elseif ParaList.kConsistencyMeasure==2
    if strcmp(Database,'YUD')
        ParaList.kInClassResidualThreshold = 0.5;
    elseif strcmp(Database,'ECD')
        ParaList.kInClassResidualThreshold = 0.5;
    end
else
    error('Please choose the correct consistency measure method. Either 1 for CM1 or 2 for CM2');
end

if strcmp(ParaList.kRefineMethod,'MLE')
    %if the MLE method is used to refine the estimation, then the GAMMA parameter should
    %be defined which is the scale parameter of the Cauchy distribution function.
    if strcmp(Database,'YUD')
        GAMMA = 0.5;
    else
        GAMMA = 1;
    end
end

ttt = clock; seed = fix(ttt(6)*1e6);
rand('twister', seed);
randn('state',  seed);

if strcmp(Database, 'YUD')
    load ./ExampleData/YUD/cameraParameters.mat %load camera intrinsic parameters 
    fid = fopen('./ExampleData/YUD/imageName.list');
    if UseLineFromDatabase
        fidLine = fopen('Please set correct path here');
    else
        fidLine = fopen('./ExampleData/YUD/lineFile.list');
    end
elseif strcmp(Database, 'ECD')
    fid     = fopen('./ExampleData/ECD/imageName.list');
    fidLine = fopen('./ExampleData/ECD/lineFile.list');    
    load ./ExampleData/ECD/ImageSizes.mat
    UseLineFromDatabase = 0;
    imageWidthVec  = imageWidthVec*0.5; %image is downsampled.
    imageHeightVec = imageHeightVec*0.5;%image is downsampled.    
else
    error('Please choose the name database:YUD or ECD.\n If other database is going to use, then the file path in the following need be adjusted.');
end

text          = textscan(fid,'%s');
imageNameList = text{1}; 
text          = textscan(fidLine,'%s');
lineNameList  = text{1}; 
imageNum      = size(imageNameList,1);

if kSaveResults == true
    outPath = 'OutResult/';
    if ~exist(outPath,'dir')
        mkdir(outPath);
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
for imageID = 1:imageNum
    % get lines from file
    lineFileName = lineNameList{imageID};
    lines_old    = load(lineFileName);    
    numOfLines = size(lines_old, 1);
    % adjust the coordinates of lines to center at the principal point( or image center)
    if  strcmp(Database, 'ECD')
        pp = 0.5*[imageWidthVec(imageID), imageHeightVec(imageID)];
    end
    center = [0, pp, pp];
    lines = zeros(numOfLines,5);    
    for i=1:numOfLines
      lines(i,:) = lines_old(i,:) - center;  
    end
    
    [bestClassification, info] = ClassifyLinesAndEstimateFocal(lines, ParaList);
    if info.success == 0
        disp('failed to estimate a valid focal length. This mainly due to the vanishing points are far from the image center.');
        continue;
    end
    if kPlotLines
        disPlayInfo1 = strcat('ID = ', num2str(imageID), ',   timeToRansac = ', num2str(info.timeToRansac),...
           ',   timeToRefine = ', num2str(info.timeToRefine),...     
           ',   Inliers = ', num2str(info.bestNumInliersRatio), ',    focal= ', num2str(info.bestFocal),...
           ',   hpyCount = ', num2str(info.hypCount));
        disp(disPlayInfo1);
        % load the image
        imageName  =  imageNameList{imageID};
        Image_orig = imread(imageName);
        fig1 = figure('Position', [10,500, 640, 480]);
        imshow(Image_orig,'Border','tight');         
         hold on
         %draw lines into image
         for i=1:numOfLines
             plot([lines_old(i,2),lines_old(i,4)], [lines_old(i,3),lines_old(i,5)],'b','LineWidth',2)
         end
         
         hold off
         if kSaveResults == true
             name = num2str(imageID, '%03d'); 
             print(strcat(outPath,name,'_Line.jpg'),'-djpeg','-r80');
         end
         % create result images
         fc = [1,1]*info.bestFocal; 
         fig2 = plot_vanishing_points(Image_orig, ...
             lines_old(bestClassification ~= 0,:), ...
             bestClassification(bestClassification ~= 0), ...
             info.bestVP, ...
             fc, pp, 0);         
         if kSaveResults == true
             print(strcat(outPath,name,'_VP.jpg'),'-djpeg','-r80');
         end
         pause;
         close([fig1, fig2]);        
    end    

end

























