function rot = eulerAngleXYZ2Rot(phiX, phiY, phiZ);
%%%this function is to convert the euler angle to rotation matrix.
%%% rot = R(phiX)*R(phiY)*R(phiZ)
Rx = zeros(3,3);
Ry = Rx;
Rz = Rx;

Rx(1,1) = 1;
Rx(2,2) = cos(phiX);
Rx(2,3) = -sin(phiX);
Rx(3,2) = -Rx(2,3);%sin(phiX)
Rx(3,3) = Rx(2,2);%cos(phiX)

Ry(1,1) = cos(phiY);
Ry(1,3) = sin(phiY);
Ry(2,2) = 1;
Ry(3,1) = -Ry(1,3); %-sin(phiY);
Ry(3,3) = Ry(1,1); %cos(phiY);

Rz(1,1) = cos(phiZ);
Rz(1,2) = -sin(phiZ);
Rz(2,1) = -Rz(1,2);
Rz(2,2) = Rz(1,1);
Rz(3,3) = 1;

rot = Rx * Ry * Rz;