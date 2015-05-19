function [rot_wc] = RefineVPByAlgLS(n_c,bestClassification)
%This function follows the AlgLS algorithm proposed by Faraz and Stergios: 
% Globally optimal pose estimation from line corrsepondences.
%input: n_c(:,i) = the normal of interprelation plane passing through to camera center and the line in camera frame;
%       V_w(:,i) = the direction of ith line in the world frame
%       bestClassification--best classification results
%output: rot_wc = the orientation of camera in rotation matrix parametrization
%                 (V_c = rot_wc * V_w)


addpath('AlgLSUtils','AlgLSUtils/Cexp','AlgLSUtils/robotics3D');%add the necessary file path

n = size(n_c,1);
if( n~=size(bestClassification,1) ) 
    error('Input data n_c,  bestClassification are inconsistent'); 
end

numInliers = sum(bestClassification ~= 0);

I_moment_n = zeros(3, numInliers); 
G_line     = zeros(3, numInliers); 
n_c = n_c';
for lineID=1:n
    if  bestClassification(lineID) == 1
        I_moment_n(:,lineID) = n_c(:,lineID);
        G_line(:,lineID)     = [1,0,0]';
    elseif bestClassification(lineID) == 2
        I_moment_n(:,lineID) = n_c(:,lineID);
        G_line(:,lineID)     = [0,1,0]';
    else
        if bestClassification(lineID) == 3
            I_moment_n(:,lineID) = n_c(:,lineID);
            G_line(:,lineID)     = [0,0,1]';
        end
    end    
end

%call Faraz's EstimateVanishingPoints() function, which returns the
%rotation matrix rot_cw in quaternion form.

[q_sols, residuals, info] = EstimateVanishingPoints(I_moment_n, G_line, 'relaxed');
rot_cw = quat2rot(q_sols);
rot_wc = rot_cw';
return