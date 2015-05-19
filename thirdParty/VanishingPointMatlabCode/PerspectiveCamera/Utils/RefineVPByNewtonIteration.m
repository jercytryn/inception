function [vp, residual] = RefineVPByNewtonIteration(linePlaneNormal,  initVP, Classification, kConsistencyMeasure,linesInImage,kMat)
%%%This function is to refine the estimated vanishing points according to the
%%%classification result by newton iteration method
%%% Input: linePlaneNormal -- the normal of the line interpretation plane in the camera frame.
%%%        initVP          -- the initial value of vanishing points
%%%        Classification  -- the line classification results
%%%        kConsistencyMeasure-- the method to compute the residual of a line with respect to a vanishing point:
%%%                           '1 for CM1' or '2 for CM2'.
%%%        linesInImage    -- the extracted lines from image; if kConsistencyMeasure=2, then this parameter is needed.
%%%        kMat            -- the camera intrinsic parameters; if kConsistencyMeasure=2, then this parameter is needed.
%%% Output: vp             -- refined vanishing points
%%%         residual       -- the residual

small   = 1e-4;
TOL     = 1e-3;% tolerance for declaration of convergence
DAMPED  = 1; %for the damped method to achieve global convergence
nmax    = 30; %maximum number of iteration steps
MaxDampCount = 10;%maximum number of iteration steps of damp process

rho = 0.5; % parameter for damped method
alpha0 =0.6;%parameter for update
vp = initVP/det(initVP); % convert to a rotation matrix

numOfLines = size(linePlaneNormal,1);
residual = zeros(numOfLines,1);

nit = 0;
zerovec3 = [0,0,0];

if kConsistencyMeasure==1%CM1
    for lineID=1:numOfLines
        class = Classification(lineID);
        residual(lineID) =  (linePlaneNormal(lineID,:)*vp(:,class))^2;
    end
    
    while((nit < nmax) && (norm(residual) > TOL))
        nit = nit + 1;
        % get derivative
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
        for lineID=1:numOfLines
            class  = Classification(lineID);
            normal = linePlaneNormal(lineID,:);
            tempVec= normal*vp(:,class)*normal;
            df_phiX(lineID) = tempVec*dVP_phiX(:,class);
            df_phiY(lineID) = tempVec*dVP_phiY(:,class);
            df_phiZ(lineID) = tempVec*dVP_phiZ(:,class);
        end
        dfMat = [df_phiX,df_phiY,df_phiZ];
        % get search direction
        delta = -inv(dfMat'*dfMat)*dfMat'*residual;
        if(norm(delta)<small)% zero derivative -> divergence of the method
            break;
        else
            alpha = alpha0; % damping parameter set to 1
            % update
            newphiX = phiX + alpha*delta(1);
            newphiY = phiY + alpha*delta(2);
            newphiZ = phiZ + alpha*delta(3);
            vp = eulerAngleXYZ2Rot(newphiX, newphiY, newphiZ);
            %compute the new residual
            residual_old_norm = norm(residual);
            for lineID=1:numOfLines
                class = Classification(lineID);
                residual(lineID) = (linePlaneNormal(lineID,:)*vp(:,class))^2;
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
                    vp = eulerAngleXYZ2Rot(newphiX, newphiY, newphiZ);
                    for lineID=1:numOfLines
                        class = Classification(lineID);
                        residual(lineID) = (linePlaneNormal(lineID,:)*vp(:,class))^2;
                    end
                end
            end
        end
    end
elseif kConsistencyMeasure==2
    %compute the middle points of image lines which equals to [0.5*(sx+ex), 0.5(sy+ey), 1]
    middlePoints        = ones(numOfLines,3);
    middlePoints(:,1:2) = 0.5*(linesInImage(:,2:3) + linesInImage(:,4:5));
    %first convert the vanishing points in space to image plane.
    V                   = kMat*vp; %vanishing point in the image;
    for i = 1:numOfLines
        mp          = middlePoints(i,:);%homogenous coordinate
        sp          = [linesInImage(i,2:3), 1]';%start point
        class       = Classification(i);        
        idealL      = cross(mp, V(:,class));
        % the distance of start points to the ideal line in the image plane.
        D           = idealL*sp/sqrt(idealL(1)*idealL(1)+idealL(2)*idealL(2));
        residual(i) = 0.5 * D * D;
    end
    
    while((nit < nmax) && (norm(residual) > TOL))
        nit = nit + 1;
        % compute the derivate
        [phiX, phiY, phiZ] = rot2EulerAngleXYZ(vp);
        cosX = cos(phiX);     sinX = sin(phiX);
        cosY = cos(phiY);     sinY = sin(phiY);
        cosZ = cos(phiZ);     sinZ = sin(phiZ);
        dV_phiX = kMat*[zerovec3; -vp(3,:); vp(2,:)];
        dV_phiY = kMat*[1,0,0; 0,cosX, -sinX;0,sinX,cosX]*...
                       [-sinY, 0, cosY; 0,0,0; -cosY,0,-sinY]*...
                       [cosZ, -sinZ,0; sinZ,cosZ,0; 0,0,1];
        dV_phiZ = kMat*[vp(:,2), -vp(:,1), zerovec3'];
        df_phiX = zeros(numOfLines,1);
        df_phiY = zeros(numOfLines,1);
        df_phiZ = zeros(numOfLines,1);
        V       = kMat*vp;
        for i=1:numOfLines
            class     = Classification(i);
            mp        = middlePoints(i,:);%middle point
            idealL    = cross(mp, V(:,class));%ideal line (i.e. l) = middle point x vanishing point in the image
            sp        = [linesInImage(i,2:3), 1]';
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
        end
        dfMat = [df_phiX,df_phiY,df_phiZ];
        % get the search direction
        delta = -inv(dfMat'*dfMat)*dfMat'*residual;
        if(norm(delta)<small)% zero derivative -> divergence of the method
            break;
        else
            alpha = alpha0; % damping parameter set to alpha0
            % update
            newphiX = phiX + alpha*delta(1);
            newphiY = phiY + alpha*delta(2);
            newphiZ = phiZ + alpha*delta(3);
            vp      = eulerAngleXYZ2Rot(newphiX, newphiY, newphiZ);
            residual_old_norm = norm(residual);
            %compute the new residual
            V       = kMat*vp;
            for i=1:numOfLines
                class     = Classification(i);
                mp        = middlePoints(i,:);
                idealL    = cross(mp, V(:,class));
                sp        = [linesInImage(i,2:3), 1]';
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
                    V       = kMat*vp;
                    for i=1:numOfLines
                        class     = Classification(i);
                        mp        = middlePoints(i,:);
                        idealL    = cross(mp, V(:,class));
                        sp        = [linesInImage(i,2:3), 1]';
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
return