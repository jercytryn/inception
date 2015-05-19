function [vp, focal, residual] = RefineVPAndFocalByNewtonIteration(lines, initVP, initFocal, Classification, kConsistencyMeasure)
%%%This function is to refine the estimated vanishing points and the camera focal length according to the
%%%classification result by newton iteration method.
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

small = 1e-4;
TOL = 1e-3;% tolerance for declaration of convergence
DAMPED = 1; %for the damped method to achieve global convergence
nmax = 30; %maximum number of iteration steps
MaxDampCount = 10;%maximum number of iteration steps of damp process

rho    = 0.5; % parameter for damped method
alpha0 =0.6;%parameter for update
vp     = initVP/det(initVP); % convert to a rotation matrix
focal  = initFocal;

numOfLines = size(lines, 1);
residual   = zeros(numOfLines,1);
nit = 0;
zerovec3 = [0,0,0];

if kConsistencyMeasure==1%CM1
    linePlaneNormal = zeros(numOfLines,3);%linePlaneNormal(i,:)=[nx,ny,nz]
    % compute the normal of the interpretation plane of each line in the camera frame.
    % We first get [nx, ny, nz] = [xs, ys, 1] x [xe, ye, 1]
    % then planeNormal = [xs, ys, focal] x [xe, ye, focal] = [focal * nx, focal * ny, nz]
    for i=1:numOfLines
        normal_c = cross([lines(i,2:3),1], [lines(i,4:5),1]);
        linePlaneNormal(i,:) = normal_c;%[nx, ny, nz] = [xs, ys, 1] x [xe, ye, 1]
        normal_c(3)          = normal_c(3)/focal;
        planeNormal          = normal_c/norm(normal_c);
        class                = Classification(i);
        residual(i)          = (planeNormal * vp(:,class))^2;
    end       
 
    while((nit < nmax) && (norm(residual) > TOL))
         nit = nit + 1;
         % compute the derivate
         [phiX, phiY, phiZ]=rot2EulerAngleXYZ(vp);
         cosX = cos(phiX);     sinX = sin(phiX);
         cosY = cos(phiY);     sinY = sin(phiY);
         cosZ = cos(phiZ);     sinZ = sin(phiZ);
         dVP_phiX = [zerovec3; -vp(3,:); vp(2,:)];
         dVP_phiY = [1,0,0; 0,cosX, -sinX;0,sinX,cosX]*...
             [-sinY, 0, cosY; 0,0,0; -cosY,0,-sinY]*...
             [cosZ, -sinZ,0; sinZ,cosZ,0; 0,0,1];
         dVP_phiZ = [vp(:,2), -vp(:,1), zerovec3'];
         df_phiX = zeros(numOfLines,1);
         df_phiY = zeros(numOfLines,1);
         df_phiZ = zeros(numOfLines,1);
         df_focal= zeros(numOfLines,1);
         for lineID=1:numOfLines
             class  = Classification(lineID);
             normal = linePlaneNormal(lineID,:);
             nx = normal(1); ny = normal(2); nz = normal(3); 
             planeNormal     = [focal*nx, focal*ny, nz];
             temp            = norm(planeNormal);
             normal          = planeNormal/temp;
             temp1           = normal*vp(:,class);
             tempVec         = temp1*normal;
             df_phiX(lineID) = tempVec*dVP_phiX(:,class);
             df_phiY(lineID) = tempVec*dVP_phiY(:,class);
             df_phiZ(lineID) = tempVec*dVP_phiZ(:,class);
             temp2           = focal*(nx*nx+ny*ny)/temp;
             temp1Vec        = temp*[nx, ny, 0] - temp2*planeNormal;
             df_focal(lineID)= temp1*temp1Vec*vp(:,class)/(temp*temp);             
         end
         dfMat = [df_phiX,df_phiY,df_phiZ, df_focal];
         % get search direction
         delta = -inv(dfMat'*dfMat)*dfMat'*residual;
         if(norm(delta)<small)% zero derivative -> divergence of the method
             break;
         else
              alpha = alpha0; % damping parameter set to alpha0
              focal_Pre = focal;
              % update
              newphiX = phiX + alpha*delta(1);
              newphiY = phiY + alpha*delta(2);
              newphiZ = phiZ + alpha*delta(3);
              vp      = eulerAngleXYZ2Rot(newphiX, newphiY, newphiZ);
              focal   = focal_Pre + alpha*delta(4);
              %compute the new residual
              residual_old_norm = norm(residual);
              for i=1:numOfLines
                  normal_c             = linePlaneNormal(i,:);%[nx, ny, nz] = [xs, ys, 1] x [xe, ye, 1]
                  normal_c(3)          = normal_c(3)/focal;
                  planeNormal          = normal_c/norm(normal_c);
                  class                = Classification(i);
                  residual(i)          = (planeNormal * vp(:,class))^2;
              end
              if (DAMPED)
                  %adjust the damping parameter until find a better solution
                  dampCount = 0;
                  while (norm(residual) >= residual_old_norm)&&(dampCount<MaxDampCount)
                      dampCount = dampCount +1;
                      alpha = rho*alpha; % damping parameter is adjusted
                      newphiX = phiX + alpha*delta(1);
                      newphiY = phiY + alpha*delta(2);
                      newphiZ = phiZ + alpha*delta(3);
                      vp      = eulerAngleXYZ2Rot(newphiX, newphiY, newphiZ);
                      focal   = focal_Pre + alpha*delta(4);
                      for i=1:numOfLines
                          normal_c             = linePlaneNormal(i,:);%[nx, ny, nz] = [xs, ys, 1] x [xe, ye, 1]
                          normal_c(3)          = normal_c(3)/focal;
                          planeNormal          = normal_c/norm(normal_c);
                          class                = Classification(i);
                          residual(i)          = (planeNormal * vp(:,class))^2;
                      end
                  end
              end%end if (DAMPED)
         end
    end

elseif  kConsistencyMeasure==2%CM2
    %compute the middle points of image lines which equals to 0.5*(sx+ex, sy+ey)
    middlePoints = 0.5*(lines(:,2:3) + lines(:,4:5));
    %first convert the vanishing points in space to image plane.
    kMat = [focal, 0, 0; 0, focal, 0; 0, 0, 1];
    V    = kMat*vp; %vanishing point in the image;
    for i = 1:numOfLines
        mp = [middlePoints(i,:) , 1];%homogenous coordinate
        sp          = [lines(i,2:3), 1]';%start point
        class       = Classification(i);        
        idealL      = cross(mp, V(:,class));
        % the distance of start points to the ideal line in the image plane.
        D           = idealL*sp/sqrt(idealL(1)*idealL(1)+idealL(2)*idealL(2));
        residual(i) = 0.5 * D * D;
    end
    
    while((nit < nmax) && (norm(residual) > TOL))
         nit = nit + 1;
         % compute the derivate
         [phiX, phiY, phiZ]=rot2EulerAngleXYZ(vp);
         cosX = cos(phiX);     sinX = sin(phiX);
         cosY = cos(phiY);     sinY = sin(phiY);
         cosZ = cos(phiZ);     sinZ = sin(phiZ);
         kMat = [focal, 0, 0; 0, focal, 0; 0, 0, 1];
         dV_phiX = kMat*[zerovec3; -vp(3,:); vp(2,:)];
         dV_phiY = kMat*[1,0,0; 0,cosX, -sinX;0,sinX,cosX]*...
                         [-sinY, 0, cosY; 0,0,0; -cosY,0,-sinY]*...
                         [cosZ, -sinZ,0; sinZ,cosZ,0; 0,0,1];
         dV_phiZ = kMat*[vp(:,2), -vp(:,1), zerovec3'];
         dV_focal= [vp(1,:); vp(2,:); zerovec3];
         df_phiX = zeros(numOfLines,1);
         df_phiY = zeros(numOfLines,1);
         df_phiZ = zeros(numOfLines,1);
         df_focal= zeros(numOfLines,1);
         V       = kMat*vp;  
         for i=1:numOfLines
             class     = Classification(i);
             mp        = [middlePoints(i,:) , 1];%middle point
             idealL    = cross(mp, V(:,class));%ideal line (i.e. l) = middle point x vanishing point in the image
             sp        = [lines(i,2:3), 1]'; 
             temp1     = idealL(1)*idealL(1)+idealL(2)*idealL(2);%temp1 = lx*lx+ly*ly
             temp2     = 1/sqrt(temp1); % temp2 = temp1^(-1/2)
             temp3     = idealL*sp; % temp3 = l^T * startPoint
             D         = temp3*temp2; % distance of start point to the ideal line
             % compute the derivate of distance with respect to the ideal line: dD_idealL
             dD_idealL = temp2*temp2*temp2*[sp(1)*temp1-temp3*idealL(1), sp(2)*temp1-temp3*idealL(2), temp1];
             % compute the derivate of ideal line with respect to the vanishing point: dIdealL_V = [middle point] x              
             dIdealL_V = [0, -mp(3), mp(2); mp(3), 0, -mp(1); -mp(2), mp(1), 0];  
             %now compute the derivate of the error function with respect to [phiX, phiY, phiZ, focal]
             tempVec   = D * dD_idealL * dIdealL_V; % df_V = df_D * dD_idealL * dIdealL_V;
             df_phiX(i) = tempVec*dV_phiX(:,class);
             df_phiY(i) = tempVec*dV_phiY(:,class);
             df_phiZ(i) = tempVec*dV_phiZ(:,class);
             df_focal(i)= tempVec*dV_focal(:,class);             
         end
         dfMat = [df_phiX,df_phiY,df_phiZ, df_focal];
         % get the search direction
         delta = -inv(dfMat'*dfMat)*dfMat'*residual;
         if(norm(delta)<small)% zero derivative -> divergence of the method
             break;
         else
              alpha = alpha0; % damping parameter set to alpha0
              focal_Pre = focal;
              % update
              newphiX = phiX + alpha*delta(1);
              newphiY = phiY + alpha*delta(2);
              newphiZ = phiZ + alpha*delta(3);
              vp      = eulerAngleXYZ2Rot(newphiX, newphiY, newphiZ);
              focal   = focal_Pre + alpha*delta(4);
              residual_old_norm = norm(residual);
              %compute the new residual       
              kMat = [focal, 0, 0; 0, focal, 0; 0, 0, 1];
              V    = kMat*vp;  
              for i=1:numOfLines
                  class     = Classification(i);
                  mp        = [middlePoints(i,:) , 1];
                  idealL    = cross(mp, V(:,class));
                  sp        = [lines(i,2:3), 1]'; 
                  D         = idealL*sp/sqrt(idealL(1)*idealL(1)+idealL(2)*idealL(2));
                  residual(i) = 0.5 * D * D;
              end
              if (DAMPED)
                  %adjust the damping parameter until find a better solution
                  dampCount = 0;
                  while (norm(residual) >= residual_old_norm)&&(dampCount<MaxDampCount)
                      dampCount = dampCount +1;
                      alpha = rho*alpha; % damping parameter is adjusted
                      newphiX = phiX + alpha*delta(1);
                      newphiY = phiY + alpha*delta(2);
                      newphiZ = phiZ + alpha*delta(3);
                      vp      = eulerAngleXYZ2Rot(newphiX, newphiY, newphiZ);
                      focal   = focal_Pre + alpha*delta(4);
                      kMat    = [focal, 0, 0; 0, focal, 0; 0, 0, 1];
                      V       = kMat*vp;
                      for i=1:numOfLines
                          class     = Classification(i);
                          mp        = [middlePoints(i,:) , 1];
                          idealL    = cross(mp, V(:,class));
                          sp        = [lines(i,2:3), 1]';
                          D         = idealL*sp/sqrt(idealL(1)*idealL(1)+idealL(2)*idealL(2));
                          residual(i) = 0.5 * D * D;
                      end
                  end
              end%end if (DAMPED)
         end
    end    
else
    error('kConsistencyMeasure must be either 1 (CM1) or 2 (CM2)');
end































