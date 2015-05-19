function [VanishingPoint, focal, numofResults] = SolveHypVPF( lines, bFast )
%This function is to compute the vanishing point from the given hypothesis which includes
%four lines with unknown relationships. For four lines, there are four possible configurations in the Manhattan world.
%   configuration1: two lines are parallel and mutually orthogonal with the other two lines;
%   configuration2: four lines are drawn in two orthogonal groups, each group includes a parallel line pair;
%   configuration3: three lines are parallel and the fourth line is orthogonal to them;
%   configuration4: all of them are parallel to each other.
%Since the last two configurations are not admissible to solve the problem, we ignore them.
%For lines in configuration1, there are 6 possible cases; 
%For lines in configuration2, there are 3 possible cases;
%In total, there are 9 possible cases:
%   case1: line1 // line2 \cdot line3 \cdot line4
%   case2: line1 // line3 \cdot line2 \cdot line4
%   case3: line1 // line4 \cdot line2 \cdot line3
%   case4: line2 // line3 \cdot line1 \cdot line4
%   case5: line2 // line4 \cdot line1 \cdot line3
%   case6: line3 // line4 \cdot line1 \cdot line2
%   case7: line1 // line2 \cdot line3 // line4
%   case8: line1 // line3 \cdot line2 // line4
%   case9: line1 // line4 \cdot line2 // line3

%input: lines -- four image lines in the Manhattan world, line(i,:) = [i, startPointx, startPointy, endPointx, endPointy]
%                Note: The principal point (or image center) is the origin of the image coordinate frame.
%       bFast -- flag to mark whether configuration1 and configuration1 need be tested.
%                1: only test case1 and case7;   0: test all nine cases
%Output: vanishingPoint -- [vaniX, vaniY, vaniZ]; 
%                           vaniX: the vanishing point of lines which are parallel to X axis. 
%                           vaniY: the vanishing point of lines which are parallel to Y axis. 
%                           vaniZ: the vanishing point of lines which are parallel to Z axis. 
%        focal          -- the focal length of the camera
%        numofResults   -- number of possible solutions

if bFast %only test case1 in configuration1 and case7 in configuration2
    
  configuration = 1;
  [vp1, foc1, num1] = EstimateVPandFocalFrom4Lines(lines, configuration);%line1 // line2 \cdot line3 \cdot line4
  configuration = 2;
  [vp7, foc7, num7] = EstimateVPandFocalFrom4Lines(lines, configuration);%line1 // line2 \cdot line3 // line4
  VanishingPoint    = [vp1, vp7];
  focal             = [foc1; foc7];
  numofResults      = num1 + num7;
  
else% test all the nine cases
    
  configuration = 1;
  [vp1, foc1, num1] = EstimateVPandFocalFrom4Lines(lines, configuration);%line1 // line2 \cdot line3 \cdot line4
  [vp2, foc2, num2] = EstimateVPandFocalFrom4Lines(lines([1,3,2,4],:), configuration);%line1 // line3 \cdot line2 \cdot line4
  [vp3, foc3, num3] = EstimateVPandFocalFrom4Lines(lines([1,4,2,3],:), configuration);%line1 // line4 \cdot line2 \cdot line3
  [vp4, foc4, num4] = EstimateVPandFocalFrom4Lines(lines([2,3,1,4],:), configuration);%line2 // line3 \cdot line1 \cdot line4
  [vp5, foc5, num5] = EstimateVPandFocalFrom4Lines(lines([2,4,1,3],:), configuration);%line2 // line4 \cdot line1 \cdot line3
  [vp6, foc6, num6] = EstimateVPandFocalFrom4Lines(lines([3,4,1,2],:), configuration);%line3 // line4 \cdot line1 \cdot line2
  
  configuration = 2;
  [vp7, foc7, num7] = EstimateVPandFocalFrom4Lines(lines([1,2,3,4],:), configuration);%line1 // line2 \cdot line3 // line4
  [vp8, foc8, num8] = EstimateVPandFocalFrom4Lines(lines([1,3,2,4],:), configuration);%line1 // line3 \cdot line2 // line4
  [vp9, foc9, num9] = EstimateVPandFocalFrom4Lines(lines([1,4,2,3],:), configuration);%line1 // line4 \cdot line2 // line3
  
  VanishingPoint = [vp1,  vp2,  vp3,  vp4,  vp5,  vp6,  vp7,  vp8,  vp9];
  focal          = [foc1; foc2; foc3; foc4; foc5; foc6; foc7; foc8; foc9];
  numofResults   = num1 + num2 + num3 + num4 + num5 + num6 + num7 + num8 + num9;  

end
