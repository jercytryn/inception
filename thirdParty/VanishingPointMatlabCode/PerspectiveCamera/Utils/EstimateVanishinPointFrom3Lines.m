function [vanishingPoint, numofResuluts] = EstimateVanishinPointFrom3Lines(lines, linePlaneNormal, configuration)
% Estimate Vanishing Points for a Calibrated Camera from 3 lines
% Input:  lines      -- three image lines in the Manhattan world, line(i,:) = [i, startPointx, startPointy, endPointx, endPointy]
%         linePlaneNormal:the normal of the line interpretation plane in the camera
%                         frame.linePlaneNormal(i,:) = [nx,ny,nz]; 
%         configuration -- flag to mark the configurations between three lines in 3D
%                       1: three lines are orthogonal to each other in 3D;
%                       2: line_1 and line_2 are parallel, line_3 is orthogonal to them. 
% Output: vanishingPoint -- [vaniX, vaniY, vaniZ]; Two groups of possible results exist for three lines.
%                           vaniX: the vanishing point of lines which are parallel to X axis. 
%                           vaniY: the vanishing point of lines which are parallel to Y axis. 
%                           vaniZ: the vanishing point of lines which are parallel to Z axis. 
%         numofResuluts  -- number of possible solutions, (0, 1 or 2)
%The key idea is that the direction of lines in camera frame is parameterized as
%  V1_c = [x1s - lambda_1 * x1e;  y1s - lambda_1 * y1e;  1 - lambda_1];
%  V2_c = [x2s - lambda_2 * x2e;  y2s - lambda_2 * y2e;  1 - lambda_2];
%  V3_c = [x3s - lambda_3 * x3e;  y3s - lambda_3 * y3e;  1 - lambda_3];
if size(lines,1) ~= 3
     error(' error in EstimateVanishinPointFrom3Lines(lines, configuration), only three lines are required.');
end

x1s = lines(1,2); y1s = lines(1,3); x1e = lines(1,4); y1e = lines(1,5); 
x2s = lines(2,2); y2s = lines(2,3); x2e = lines(2,4); y2e = lines(2,5); 
x3s = lines(3,2); y3s = lines(3,3); x3e = lines(3,4); y3e = lines(3,5); 

switch configuration
    case 1 %three lines are orthogonal to each other in 3D;
        % line_1 is orthogonal to line_2
        a0 =   x1s*x2s + y1s*y2s + 1;
        a1 = -(x1e*x2s + y1e*y2s + 1);
        a2 = -(x1s*x2e + y1s*y2e + 1);
        a3 =   x1e*x2e + y1e*y2e + 1;
        % line_1 is orthogonal to line_3
        b0 =   x1s*x3s + y1s*y3s + 1;
        b1 = -(x1e*x3s + y1e*y3s + 1);
        b2 = -(x1s*x3e + y1s*y3e + 1);
        b3 =   x1e*x3e + y1e*y3e + 1;
        % line_2 is orthogonal to line_3
        c0 =   x2s*x3s + y2s*y3s + 1;
        c1 = -(x2e*x3s + y2e*y3s + 1);
        c2 = -(x2s*x3e + y2s*y3e + 1);
        c3 =   x2e*x3e + y2e*y3e + 1;      
        % f(lambda1) = w0 + w1 * lambda1 + w2 * lambda1^2;
        w0 = a0*b0*c3 - a2*b0*c2 - a0*b2*c1 + a2*b2*c0;
        w1 = a1*b0*c3 - a3*b0*c2 + a0*b1*c3 - a2*b1*c2 - a0*b3*c1 + a2*b3*c0 - a1*b2*c1 + a3*b2*c0;
        w2 = a1*b1*c3 - a3*b1*c2 - a1*b3*c1 + a3*b3*c0;
        % solve lambda1 from the 2 degree polynomial;
        rs= roots([w2, w1, w0]);
        % only keep the real roots
        maxreal= max(abs(real(rs)));
        rs(abs(imag(rs))/maxreal > 0.001)= [];
        lambda_1 = real(rs);
        numofResuluts = size(lambda_1,1);
        if numofResuluts == 0
            vanishingPoint = [];
            return;
        end
        vanishingPoint = zeros(3, numofResuluts*3);
        for id = 1: numofResuluts
            lambda_2 = - (a1*lambda_1(id) + a0)/(a3*lambda_1(id) + a2);
            lambda_3 = - (b1*lambda_1(id) + b0)/(b3*lambda_1(id) + b2);
            
            temp = [x1s - lambda_1(id) * x1e;  y1s - lambda_1(id) * y1e;  1 - lambda_1(id)];
            vanishingPoint(:,id*3 - 2) =  temp/norm(temp); %vaniX = V1_c
            
            temp = [x2s - lambda_2 * x2e;  y2s - lambda_2 * y2e;  1 - lambda_2];
            vanishingPoint(:,id*3 - 1) =  temp/norm(temp); %vaniY = V2_c
            
            temp = [x3s - lambda_3 * x3e;  y3s - lambda_3 * y3e;  1 - lambda_3];
            vanishingPoint(:,id*3 - 0) =  temp/norm(temp); %vaniZ = V3_c           
        end
        
    case 2 %line_1 and line_2 are parallel, line_3 is orthogonal to them. 
        % line_1 is parallel to line_2
        a0 =   x1s - x2s;
        a1 = -(x1e - x2s);
        a2 = -(x1s - x2e);
        a3 =   x1e - x2e;
        
        b0 =   y1s - y2s;
        b1 = -(y1e - y2s);
        b2 = -(y1s - y2e);
        b3 =   y1e - y2e;
        % line_1 is orthogonal to line_3
        c0 =   x1s*x3s + y1s*y3s + 1;
        c1 = -(x1e*x3s + y1e*y3s + 1);
        c2 = -(x1s*x3e + y1s*y3e + 1);
        c3 =   x1e*x3e + y1e*y3e + 1;
        % f(lambda1) = w0 + w1 * lambda1 + w2 * lambda1^2;
        w0 = a2*b0 - a0*b2;
        w1 = a2*b1 + a3*b0 - a0*b3 - a1*b2;
        w2 = a3*b1 - a1*b3;
        % solve lambda1 from the 2 degree polynomial;
        rs= roots([w2, w1, w0]);
        % only keep the real roots
        maxreal= max(abs(real(rs)));
        rs(abs(imag(rs))/maxreal > 0.001)= [];
        lambda_1 = real(rs);
        numofResuluts = size(lambda_1,1);
        if numofResuluts == 0
            vanishingPoint = [];
            return;
        end
        vanishingPoint = zeros(3, numofResuluts*3);
        for id = 1: numofResuluts
            lambda_3 = - (c1*lambda_1(id) + c0)/(c3*lambda_1(id) + c2);
            
            tempX = [x1s - lambda_1(id) * x1e;  y1s - lambda_1(id) * y1e;  1 - lambda_1(id)];
            vanishingPoint(:,id*3 - 2) =  tempX/norm(tempX); %vaniX = V1_c = V2_c; Because they are parallel.
            
            tempY = [x3s - lambda_3 * x3e;  y3s - lambda_3 * y3e;  1 - lambda_3];
            vanishingPoint(:,id*3 - 1) =  tempY/norm(tempY); %vaniY = V3_c;
            
            tempZ = cross(tempX, tempY); 
            vanishingPoint(:,id*3 - 0) =  tempZ/norm(tempZ); %vaniZ = vaniX x vaniY; 
        end
    otherwise
         error(' error in EstimateVanishinPointFrom3Lines(lines, configuration), configuration must be either 1 or 2');   
end
        
%verify the results.
%we notice that if three lines are assigned a wrong configuration, 
%then n_c * V_c =0 cann't be hold in general. 
if numofResuluts==1
    err = zeros(1,3);
    if configuration ==1
        err(1) = linePlaneNormal(1,:) * vanishingPoint(:,1);
        err(2) = linePlaneNormal(2,:) * vanishingPoint(:,2);
        err(3) = linePlaneNormal(3,:) * vanishingPoint(:,3);        
    else %configuration ==2
        err(1) = linePlaneNormal(1,:) * vanishingPoint(:,1);
        err(2) = linePlaneNormal(2,:) * vanishingPoint(:,1);
        err(3) = linePlaneNormal(3,:) * vanishingPoint(:,2);  
    end
    if norm(err)>1e-3
        numofResuluts  = 0;
        vanishingPoint = [];
    end
else%numofResuluts==2
    err = zeros(1,6);
    if configuration ==1
        for i =1:3
            n_c = linePlaneNormal(i,:);% the normal of the line interpretation plane.
            err(i)   = n_c*vanishingPoint(:,i);
            err(i+3) = n_c*vanishingPoint(:,i+3);
        end
    else %configuration ==2
        %test line 1
        n_c = linePlaneNormal(1,:);% the normal of the line interpretation plane.
        err(1) = n_c*vanishingPoint(:,1);
        err(4) = n_c*vanishingPoint(:,4);
        %test line 2
        n_c = linePlaneNormal(2,:);% the normal of the line interpretation plane.
        err(2) = n_c*vanishingPoint(:,1);
        err(5) = n_c*vanishingPoint(:,4);
        %test line 3
        n_c = linePlaneNormal(3,:);% the normal of the line interpretation plane.
        err(3) = n_c*vanishingPoint(:,2);
        err(6) = n_c*vanishingPoint(:,5);
    end
    
    if norm(err(1:3))>1e-3 && norm(err(4:6))>1e-3
        numofResuluts  = 0;
        vanishingPoint = [];
    elseif norm(err(1:3))<=1e-3 && norm(err(4:6))>=1e-3
        numofResuluts  = 1;
        vanishingPoint = vanishingPoint(:,1:3);
    elseif norm(err(1:3))>1e-3 && norm(err(4:6))<=1e-3
        numofResuluts  = 1;
        vanishingPoint = vanishingPoint(:,4:6);
    end
end
return