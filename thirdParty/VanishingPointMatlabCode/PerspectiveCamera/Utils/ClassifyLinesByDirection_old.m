function [bestClassification, info] = ClassifyLinesByDirection(lines, kMaxNumHyp, kMinNumHyp, kAcceptHypotheseThreshold, kInClassResidualThreshold)
%%This function is to classify lines according to their directions in the Manhattan world.
%Input:  lines      --  the extracted lines from image, line(i,:) = [i, startPointx, startPointy, endPointx, endPointy]
%        kMaxNumHyp --  the max number of hypotheses generated in ransac procedure. The
%                       adaptive method (see Hartley and Zisserman, p. 120) for determining number
%                       of hypotheses will stop when reaches this number.
%        kMinNumHyp --  the min number of hypotheses in ransac procedure that will be
%                       generated before adaptive method (see Hartley and Zisserman, p. 120) kicks in.
%        kAcceptHypotheseThreshold -- threshold to accept a hypothesis. When more than 85% inliers are established
%                                     by a hypothesis, then stop test the other hypotheses.
%        kInClassResidualThreshold -- the threshold to decide whether to accept a line within a class (Xdir, Ydir, Zdir)
%Output: bestClassification -- A row vectors with numbers from 0-3, corresponding to each line input in
%                              lines argument. 0 indicates the outliers, and 1-3 denote one of the three
%                              cardinal classed assigned to the line.
%        info --  A data structure containing basic debugging information. The field names
%                 are self explanatory.

timeStart = tic;
% get the number of lines
numOfLines = size(lines,1);

linePlaneNormal = zeros(numOfLines,3);%store interpretation plane normal,linePlaneNormal(i,:)=[nx,ny,nz]
% compute the normal of interpretation plane of each line
for i=1:numOfLines
    normal_c = cross([lines(i,2:3),1], [lines(i,4:5),1]);% the normal of the line interpretation plane in camera frame.
    normal_c = normal_c/norm(normal_c);
    linePlaneNormal(i,:) = normal_c;
end

%first compute the histogram of image line directions.
%because we believe that in general, there are at least two clusters of image 
%line directions if they passing through at least two vanishing points.
%This maybe invalid in some special cases, so the RANSAC approach is still employed.
histogramLen = 15;% the resolution of each bin is pi/15rad, i.e.12degree.
dirHistogram = zeros(histogramLen,1);%store the histogram of image line directions.
dirCell      = cell(histogramLen,1);%store line IDs in each cell. 
resolution   = pi/histogramLen;
dx = lines(:,4) - lines(:,2);% dx = ex-sx;
dy = lines(:,5) - lines(:,3);% dy = ey-sy;
for lineID = 1: numOfLines
    dir   = atan(dy(lineID)/dx(lineID));% range from -pi/2 to pi/2.
    binID = max(ceil((dir+pi/2)/resolution),1); % when dy<0 and dx=0, dir will be -pi/2, then cell((dir+pi/2)/resolution) = 0;
    dirHistogram(binID) = dirHistogram(binID) + 1; 
    dirCell{binID}      = [dirCell{binID}, lineID];
end
%pick the bin which includes the largest number of lines
[numLinesInpeak1, peakID1] = max(dirHistogram);
dirHistogram(peakID1) = 0;
%pick the bin which includes the second largest number of lines
[numLinesInpeak2, peakID2] = max(dirHistogram);

%separate the input lines according to two situations.
%situationA: the largest and second largest groups of lines relative to
%             two Manhattan directions. Then the hypotheses are only
%             generated from lines in these two groups.
%situationB: only the largest group of lines relative to 
%            one Manhattan directions. Then the hypotheses are generated
%            from all lines.
lineIDPart1AB = dirCell{peakID1}; %all the lines in the peakID1 bin forms first part for both situations.
lineIDPart2A  = dirCell{peakID2}; %all the lines in the peakID2 bin forms second part for situationA.
lineIDPart2B  = [];

for binID = 1:histogramLen
    %all the lines not in the peakID1 bin forms second part for situationB.
    if binID ~= peakID1        
        lineIDPart2B = [lineIDPart2B, dirCell{binID}];
    end
end

%The following code is to use RANSAC to find the best set of hypotheses.
%Each set of hypotheses are formed from two parts. 
%The first part includes two randomly picked lines from lineIDPart1AB for
%both situations. 
%The second part includes a randomly picked line from lineIDPart2A for
%situationA or from lineIDPart2B for situationB.

%now generate the first part of unique random hypotheses for both situations.
%generate more hypotheses to ensure enouph unique hypotheses available
kMaxNumHyp = min(kMaxNumHyp, numLinesInpeak1*(numLinesInpeak1-1)*0.5);%in case a few number of lines in image
randomValues = rand(ceil(kMaxNumHyp*2),2);
randomHypoth = ceil(randomValues*numLinesInpeak1);
%pick kMaxNumHyp unique hypotheses;
hypoth1AB = zeros(kMaxNumHyp,2);
hypoth1AB(1,:) = randomHypoth(1,:);%initialize the first hypothesis
currentHypothID = 1;
for candidateID = 2:size(randomHypoth,1)
    lineID1  = randomHypoth(candidateID,1);
    lineID2  = randomHypoth(candidateID,2);
    if lineID1>0&&lineID2>0
        bExisted = 0;
        %check whether  [lineID1 lineID2] exist in hypoth1AB
        for hypothID = 1:currentHypothID
            lineIDOld1 = hypoth1AB(hypothID, 1);
            lineIDOld2 = hypoth1AB(hypothID, 2);
            if (lineID1==lineIDOld1&&lineID2==lineIDOld2) || (lineID1==lineIDOld2&&lineID2==lineIDOld1)
                bExisted = 1;
                break;
            end
        end
        %[lineID1 lineID2] is not existed, it's a new valid hypothesis
        if bExisted == 0
            currentHypothID = currentHypothID + 1;
            hypoth1AB(currentHypothID,:) = [lineID1 lineID2];
        end
        %generated enough valid hypotheses
        if currentHypothID == kMaxNumHyp
            break;
        end
    end
end

%Initialize the best results
bestClassification = zeros(numOfLines,1);
bestVPXYZ          = zeros(3,3);
bestHypothesis     = [];
bestNumInliers     = 0;

%Consider situation A.
%Generate the second part of unique random hypotheses for situations A.
hypoth2A = ceil(numLinesInpeak2 * rand(kMinNumHyp*2,1));%only kMinNumHyp hypotheses for situation A.


%test all kMinNumHyp hypotheses for situation A.
bFast = 1;
for hypCount = 1:kMinNumHyp
    % get the sample subset
    lineID1 = lineIDPart1AB(hypoth1AB(hypCount,1));
    lineID2 = lineIDPart1AB(hypoth1AB(hypCount,2));
    lineID3 = lineIDPart2A(hypoth2A(hypCount));
    hypSelectLines = [lineID1, lineID2, lineID3];
    % compute the vanishing points for this subset
    [vanishingPoint, numofResults] = SolveHypVP( lines(hypSelectLines,:), linePlaneNormal(hypSelectLines,:), bFast);
    % count the inliers, if more than previous, update the best hypotheses
    for resulutsID = 1: numofResults
        newClassification = zeros(numOfLines,1);
        vpXYZ = vanishingPoint(:,3*resulutsID-2 : 3*resulutsID);
        for lineID = 1:numOfLines
            res = abs(linePlaneNormal(lineID,:) * vpXYZ);
            [minRes, minClass] = min(res);
            % if one of the residuals is less than threshold, classify the line accordingly
            if minRes < kInClassResidualThreshold
                newClassification(lineID) = minClass;
            end
        end
        newNumInliers = sum(newClassification ~= 0);
        % if more inliers are detected with this hyp, update the best hyp
        if newNumInliers > bestNumInliers
             bestNumInliers     = newNumInliers;
             bestClassification = newClassification;
             bestVPXYZ          = vpXYZ;
             bestHypothesis = hypSelectLines;
        end
        if bestNumInliers/numOfLines > kAcceptHypotheseThreshold
            break;
        end
    end
    if bestNumInliers/numOfLines > kAcceptHypotheseThreshold
        break;
    end
end


if bestNumInliers/numOfLines > kAcceptHypotheseThreshold
   %more than needed number of hypotheses have been tested. For example, when
   %neededNumHyp<5, means 90% of lines are grouded in Manhattan world directions.
   bestHypInSituation = 'A';
else
   bestHypInSituation = 'B';
   bFast = 0;
   %less than number of hypotheses have been tested.
   %now we consider situation B. and employ the adaptive RANSAC method.
   %number of lines in lineIDPart2B = (numOfLines-numLinesInpeak1);  
   hypoth2B = ceil((numOfLines-numLinesInpeak1) * rand(kMaxNumHyp*2,1)); %at most kMaxNumHyp hypotheses for situation B.
   log01 = log(0.01);
   % hypotheses  evaluation loop
   numHyp = kMaxNumHyp;% numHyp will be adaptive adjusted.
   hypCount = 0;
   while hypCount < numHyp
       hypCount = hypCount + 1;
       % get the sample subset
       lineID1 = lineIDPart1AB(hypoth1AB(hypCount,1));
       lineID2 = lineIDPart1AB(hypoth1AB(hypCount,2));
       lineID3 = lineIDPart2B(hypoth2B(hypCount));
       hypSelectLines = [lineID1, lineID2, lineID3];
       % compute the vanishing points for this subset
       [vanishingPoint, numofResults] = SolveHypVP( lines(hypSelectLines,:), linePlaneNormal(hypSelectLines,:), bFast);
       % count the inliers, if more than previous, update the best hypotheses
       for resulutsID = 1: numofResults
           newClassification = zeros(numOfLines,1);
           vpXYZ = vanishingPoint(:,3*resulutsID-2 : 3*resulutsID);
           for lineID = 1:numOfLines
               res = abs(linePlaneNormal(lineID,:) * vpXYZ);
               [minRes, minClass] = min(res);
               % if one of the residuals is less than threshold, classify the line accordingly
               if minRes < kInClassResidualThreshold
                   newClassification(lineID) = minClass;
               end
           end
           newNumInliers = sum(newClassification ~= 0);
           % if more inliers are detected with this hyp, update the best hyp
           if newNumInliers > bestNumInliers
               bestNumInliers = newNumInliers;
               bestClassification = newClassification;
               bestVPXYZ          = vpXYZ;
               bestHypothesis = hypSelectLines;
               newNumHyp = ceil(log01/log(1-(newNumInliers/numOfLines)^3)); %adaptive adjustment
               numHyp = min(kMaxNumHyp,newNumHyp);
           end
           if bestNumInliers/numOfLines > kAcceptHypotheseThreshold
               break;
           end
       end
       if bestNumInliers/numOfLines > kAcceptHypotheseThreshold
           break;
       end
   end
end


% finally, refinement the bestQuat estimate, and re-classify
% choose the largest two classes in Manhattan world. Because for some images, the third
% class has only a few lines.
numClassOne   = sum(bestClassification == 1);
numClassTwo   = sum(bestClassification == 2);
numClassThree = sum(bestClassification == 3);
Temp = [numClassOne, numClassTwo, numClassThree];
[numTop1Class, Top1Class] = max(Temp);%the class has the largest number of lines
Temp(Top1Class) = 0;
[numTop2Class, Top2Class] = max(Temp);%the class has the second largest number of lines
Top3Class = 6 - Top1Class - Top2Class;
%according to lines in the Top1Class and Top2Class to estimate vanishing point 1 and 2 in Manhattan world.
Mat1 = zeros(numTop1Class,3);
Mat2 = zeros(numTop2Class,3);
rowID1 = 1;
rowID2 = 1;
for  lineID = 1:numOfLines
    if bestClassification(lineID) == Top1Class
        Mat1(rowID1,:) = linePlaneNormal(lineID,:);
        rowID1 = rowID1 + 1;
    elseif bestClassification(lineID) == Top2Class
        Mat2(rowID2,:) = linePlaneNormal(lineID,:);
        rowID2 = rowID2 + 1;
    end
end
[UMat1, SMat1, VMat1] = svd(Mat1);
vp1 = VMat1(:,3);% the last column of Vmat1;
vp1 = vp1/norm(vp1);
[UMat2, SMat2, VMat2] = svd(Mat2);
vp2 = VMat2(:,3);% the last column of Vmat2;
vp2 = vp2/norm(vp2);
%the third vanishing point in Manhattan world must be orthogonal to vp1 and vp2;
vp3 = cross(vp1, vp2);
vp3 = vp3/norm(vp3);
%vp1 and vp2 may not be exactly orthogonal to each other due to the noise, so we adjust
%them to be orthogonal.
theta = acos(vp1'*vp2);%the angle between vp1 and vp2, theta = [0, pi];
beta  = 0.5*(0.5*pi - theta);% the angle needed be rotated for vp1 and vp2 to make them orthogonal.
rot   = axisAndangle2rot(vp3, beta);
vp1bar = rot  * vp1;
vp2bar = rot' * vp2;
if abs(vp1bar'*vp2bar) > 1e-4%should rotate vp1 and vp2 by the opposite way
    vp1bar = rot' * vp1;
    vp2bar = rot  * vp2;
end
%now we get three orthogonal vanishing points.
refinedBestVPXYZ = zeros(3,3);
refinedBestVPXYZ(:,Top1Class) = vp1bar;
refinedBestVPXYZ(:,Top2Class) = vp2bar;
refinedBestVPXYZ(:,Top3Class) = vp3;
%re-classfify.
newClassification = zeros(1,numOfLines);
for lineID = 1:numOfLines
    res = abs(linePlaneNormal(lineID,:) * refinedBestVPXYZ);
    [minRes, minClass] = min(res);    
    if minRes < kInClassResidualThreshold
        newClassification(lineID) = minClass;
    end
end
bestClassification = newClassification;
% create the output argument
info.oldBestVp= bestVPXYZ;
info.bestVP   = refinedBestVPXYZ;
info.hypCount = hypCount;
info.bestNumInliersRatio= bestNumInliers/numOfLines;
info.bestHypInSituation = bestHypInSituation;
info.bestHypothesis = bestHypothesis;
info.timeClassifyLines = toc(timeStart);
return