function [phiX, phiY, phiZ]=rot2EulerAngleXYZ(rot)
%%%this function is to convert the rotation matrix to euler angle.
%%% rot = R(phiX)*R(phiY)*R(phiZ)
if rot(1,3)==1.0||rot(1,3)==-1.0
    error('Rotation for Y-axis is +-PI/2, can not decompose X-/Z-component!');
end
phiY = asin(rot(1,3));
if phiY==NaN || phiY==Inf
    error('phiY = NaN or Inf ');
end
phiX = atan2(-rot(2,3),rot(3,3));
phiZ = atan2(-rot(1,2),rot(1,1));
return
