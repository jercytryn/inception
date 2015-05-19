function [VanishingPoint, numofResults] = SolveHypVP( lines, linePlaneNormal, bFast )
%This function is to compute the vanishing point from the given hypothesis which includes three
%lines with unknown relationships. 
%For three lines, there are 3 cases of configurations in Manhattan world.
%case1: three lines are orthogonal to each in space.
%case2: two lines are parallel and the third line is orthogonal to them.
%case3: three lines are parallel to each other. Since in this case, there
%       are infinite number of camera orientations, so we ignore this case.
%input: lines -- three image lines in the Manhattan world, line(i,:) = [i,
%                startPointx, startPointy, endPointx, endPointy]
%       linePlaneNormal--the normal of the line interpretation plane in the camera frame.
%       bFast -- flag to mark whether case1 and case2 need be tested.
%                1: only test case2, 0: test case1 and case2
%Output: vanishingPoint -- [vaniX, vaniY, vaniZ]; 
%                           vaniX: the vanishing point of lines which are parallel to X axis. 
%                           vaniY: the vanishing point of lines which are parallel to Y axis. 
%                           vaniZ: the vanishing point of lines which are parallel to Z axis. 
%        numofResults  -- number of possible solutions

%first, find the solution of case 1.
vp1  = [];   vp3  = [];  vp4  = [];
num1 = 0;    num3 = 0;   num4 = 0;

if bFast == 0
    configuration = 1;
    [vp1, num1] = EstimateVanishinPointFrom3Lines(lines,linePlaneNormal, configuration);
end
%second, find the solution of case 2. 
%for case2, there are three possible solutions. 
%i.e. line1 // line2, line1 // line3, or line2// line3
configuration = 2;
[vp2, num2] = EstimateVanishinPointFrom3Lines(lines,linePlaneNormal, configuration);%line1 // line2
if bFast == 0
    [vp3, num3] = EstimateVanishinPointFrom3Lines(lines([1,3,2],:),linePlaneNormal([1,3,2],:), configuration);%line1 // line3
    [vp4, num4] = EstimateVanishinPointFrom3Lines(lines([2,3,1],:),linePlaneNormal([2,3,1],:), configuration);%line2 // line3
end
VanishingPoint = [vp1,vp2,vp3,vp4];
numofResults  = num1 + num2 + num3 + num4;
end
