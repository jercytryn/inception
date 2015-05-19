function [vp, focal, residual] = RefineVPAndFocalByMLE(lines, initVP, initFocal, Classification, kConsistencyMeasure)
%%%This function is to refine the estimated vanishing points and the camera focal length according to the
%%%classification result by a maximum likelihood estimator. 
%%%The maximum likelihood problem is solved by the BFGS algorithm offered in Matlab fminunc.m
%%%Input: lines -- image lines in the Manhattan world, line(i,:) = [i, startPointx, startPointy, endPointx, endPointy]
%%%                Note: The principal point (or image center) is the origin of the image cooridinate frame.
%%%       initVP    -- the initial value of vanishing points
%%%       initFocal -- the initial value of the camera focal length
%%%       Classification -- the line classification results
%%%       kConsistencyMeasure-- the method to compute the residual of a line with respect to a vanishing point:
%%%                             '1 for CM1' or '2 for CM2'. 
%%% Output: vp       -- the refined vanishing points
%%%         focal    -- the refined camera focal length
%%%         residual -- the residual

%THETA will be used in the evaluation function.
%THETA is the prior of the class of lines which is initialized using population size estimated from RANSAC's
%inlier set and is kept fixed during optimation.
%GAMMA is the scale parameter of the Cauchy distribution function.
%LINEPLANENORMAL will be used in the evaluation function for CM1.
%STARTPOINTS, MIDDLEPOINTS will be used in the evaluation function for CM2.
global  THETA GAMMA LINEPLANENORMAL STARTPOINTS MIDDLEPOINTS

numOfLines = size(lines, 1);
 
THETA        = zeros(1,4);
THETA(1)     = sum(Classification == 1)/numOfLines;
THETA(2)     = sum(Classification == 2)/numOfLines;
THETA(3)     = sum(Classification == 3)/numOfLines;
THETA(4)     = sum(Classification == 0)/numOfLines;%outlier

vp           = initVP/det(initVP); % convert to a rotation matrix
[phiX, phiY, phiZ] = rot2EulerAngleXYZ(vp);
X0           = [phiX, phiY, phiZ, initFocal]; %parameters [phiX, phiY, phiZ, focal]

if kConsistencyMeasure==1
    GAMMA           = 1/(2*pi);
    LINEPLANENORMAL = zeros(numOfLines,3);%linePlaneNormal(i,:)=[nx,ny,nz]
    for i=1:numOfLines
        %[nx, ny, nz] = [xs, ys, 1] x [xe, ye, 1]
        LINEPLANENORMAL(i,:) = cross([lines(i,2:3),1], [lines(i,4:5),1]);        
    end
    options = optimset('LargeScale','off', 'HessUpdate', 'bfgs');%, 'MaxFunEvals', 50, 'MaxIter', 100
    [X,residual] = fminunc(@funCM1, X0,options);
    vp           = eulerAngleXYZ2Rot(X(1), X(2), X(3));
    focal        = X(4);
elseif kConsistencyMeasure==2%CM2
    STARTPOINTS  = lines(:,2:3);
    MIDDLEPOINTS = 0.5*(STARTPOINTS + lines(:,4:5));
    
    options = optimset('LargeScale','off', 'HessUpdate', 'bfgs');%, 'MaxFunEvals', 50, 'MaxIter', 100
    [X,residual] = fminunc(@funCM2, X0,options);
    vp           = eulerAngleXYZ2Rot(X(1), X(2), X(3));
    focal        = X(4);
else
    error('kConsistencyMeasure must be either 1 (CM1) or 2 (CM2)');
end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%the evaluation function for CM1
function f = funCM1(x)
global  THETA GAMMA LINEPLANENORMAL  
numOfLines = size(LINEPLANENORMAL, 1);
scalar     = GAMMA/(2*pi);
GAMMA2     = GAMMA*GAMMA;
pro_outlier= scalar/(0.6169+GAMMA2);%the probality of a line being an outlier (pi/4 rad);
vp         = eulerAngleXYZ2Rot(x(1), x(2), x(3));
f          = 0;
for lineID = 1:numOfLines
    planeNormal    = LINEPLANENORMAL(lineID, :);
    planeNormal(3) = planeNormal(3)/x(4);%x(4) = focal
    planeNormal    = planeNormal/norm(planeNormal);
    res            = asin(planeNormal * vp);%[-pi/2, pi/2]
    %the angle distribution is resembled by a Cauchy distribution     
    probability    = scalar./(res.*res+GAMMA2);
    %the likelihood model of line corresponding to a Manhattan direction
    likelihood     = THETA.*[probability, pro_outlier];
    f              = f - log(sum(likelihood));
end

return


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%the evaluation function for CM2
function f = funCM2(x)
global  THETA GAMMA STARTPOINTS MIDDLEPOINTS  

numOfLines = size(STARTPOINTS, 1);
kMat       = [x(4), 0, 0; 0, x(4), 0; 0, 0, 1];
V          = kMat*eulerAngleXYZ2Rot(x(1), x(2), x(3));
scalar     = GAMMA/pi;
GAMMA2     = GAMMA*GAMMA;
pro_outlier= scalar/(25+GAMMA2);%the probality of a line being an outlier (5 pixels);
f          = 0;
for i = 1:numOfLines
    mp          = [MIDDLEPOINTS(i,:) , 1];%homogenous coordinate
    sp          = [STARTPOINTS(i,:), 1];%start point
    mpSkew      = [0, -mp(3), mp(2); mp(3), 0, -mp(1); -mp(2), mp(1), 0]; % [mp]x
    idealLines  = mpSkew * V;% three ideal lines
    distances   = abs(sp * idealLines);%[sp*idealLine1, sp*idealLine2, sp*idealLine3];
    temp        = idealLines(1,:).*idealLines(1,:)+idealLines(2,:).*idealLines(2,:);
    dist_Squa   = distances.*distances./temp; %distances^2    
    %the distance distribution is resembled by a Cauchy distribution     
    probability = scalar./(dist_Squa+GAMMA2);
    %the likelihood model of line corresponding to a Manhattan direction
    likelihood  = THETA.*[probability, pro_outlier];
    f           = f - log(sum(likelihood));
end

return
