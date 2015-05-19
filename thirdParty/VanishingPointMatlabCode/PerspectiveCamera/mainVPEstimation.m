%detect the vanishing points of the calibrated image
% RANSAC Run on York Urban Database
disp('------------------------------------------------------')
clear;
clc;


addpath('Utils');

ttt = clock; seed = fix(ttt(6)*1e6);

rand('twister',seed);
randn('state',seed);

load ./ExampleData/YUD/Manhattan_Image_DB_Names.mat%load image names, Please set correct paht first
load ./ExampleData/YUD/cameraParameters.mat%load camera intrinsic parameters

fc = [1,1]*focal/pixelSize; cc = pp; alpha_c = 0;

kPlotLines           = true; %flag to decide whether lines are ploted into images
kSaveResults         = false;%flag to decide whether the results are stored into disk
kUseLineFromDatabase = 0;    %0:use extracted lines, 1:use lines from database

ParaList.kMaxNumHyp                = 100;%the max number of hypotheses generated in ransac procedure.
ParaList.kMinNumHyp                = 40;%the min number of hypotheses generated in ransac procedure.
ParaList.kAcceptHypothesisThreshold= 0.90;%threshold to accept a hypothesis. When more than 85% inliers are estabilshed by a hypothesis, then stop test the other hypotheses.
ParaList.kRefineMethod             ='Iter'; %the way to refine the estimated vanishing points and classification results:  'SVD', 'Iter' or 'AlgLS'.
ParaList.kConsistencyMeasure       = 1;%the method to compute the residual of a line with respect to a vanishing point: '1 for CM1' or '2 for CM2'.

if ParaList.kConsistencyMeasure == 1
    %threshold to decide whether to accept a line within a class (Xdir, Ydir, Zdir)
    ParaList.kInClassResidualThreshold = 0.03;%unit: rad
elseif ParaList.kConsistencyMeasure==2
    ParaList.kInClassResidualThreshold = 0.8;%unit:pixel
    ParaList.kMat = [fc(1), 0, cc(1); 0, fc(2), cc(2); 0, 0, 1];%camera parameters
else
    error('Please choose the correct consistency measure method. Either 1 for CM1 or 2 for CM2');
end


if kSaveResults == true
    out_path = 'YUDB_Calib_1/';
    if ~exist(out_path,'dir')
        mkdir(out_path);
    end
end


ImageNum = size(Manhattan_Image_DB_Names,1);



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
for main_counter = 1:2 %ImageNum
    
    % load the image
    name = Manhattan_Image_DB_Names{main_counter}(1:end-1);
    in_path = strcat('./ExampleData/YUD/',name,'/');  %Please set the correct file path first
    if kPlotLines
        Ic = imread(strcat(in_path,name,'.jpg'));
    end
    % get lines from file
    if kUseLineFromDatabase == 1
        lineFileName = strcat(in_path,name,'LinesAndVP.mat');
        load(lineFileName);
        numOfEndPoint = size(lines,1)/2;
        lines_Old = zeros(numOfEndPoint,5);
        for i = 1:numOfEndPoint
            lines_Old(i,:) = [i, lines(2*i-1,:), lines(2*i,:) ];
        end
    else
        lineFileName = strcat('./ExampleData/YUD/ExtractedLines/',name,'.txt'); %Please set the correct file path first
        lines_Old = load(lineFileName);
    end
    numOfLines = size(lines_Old, 1);
    if kPlotLines
        fig1 = figure('Position', [10,500, 640,480]);
        imshow(Ic,'Border','tight');
        %draw lines into image
        hold on
        for i=1:numOfLines
            plot([lines_Old(i,2),lines_Old(i,4)], [lines_Old(i,3),lines_Old(i,5)],'b','LineWidth',2)
        end
        hold off
    end
    
    % normalize lines to unit focal length
    lines = normalize_lines(lines_Old,fc,cc);
    
    [bestClassification, info] = ClassifyLinesWithKnownFocal(...
        lines,  ParaList, lines_Old);
    
    
    % create result images
    if kPlotLines
        disPlayInfo1 = strcat('ID = ', num2str(main_counter), ',  name = ', name, ',  costTime = ', num2str(info.timeClassifyLines),...
            ',   Inliers = ', num2str(info.bestNumInliersRatio), ',    Situation= ', info.bestHypInSituation,...
            ',   hpyCount = ', num2str(info.hypCount));
        disp(disPlayInfo1);
        fig2 = plot_vanishing_points(Ic, ...
            lines_Old(bestClassification ~= 0,:), ...
            bestClassification(bestClassification ~= 0), ...
            info.bestVP, ...
            fc, cc, alpha_c);
        if kSaveResults == true
            print(strcat(out_path,name,'_VP2.jpg'),'-djpeg','-r80')
        end
        pause;
        close([fig1, fig2]);
    end
end
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%




