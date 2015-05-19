function [vanishingPoint, focal, numofResuluts] = EstimateVPandFocalFrom4Lines(lines, configuration)
% Estimate vanishing points and focal length for an uncalibrated camera from 4 lines.
% Input:  lines         -- four image lines in the Manhattan world, line(i,:) = [i, startPointx, startPointy, endPointx, endPointy]
%                          Note: The principal point (or image center) is the origin of the image coordinate frame.
%         configuration -- flag to mark the configurations between four lines in 3D
%                       1: line_1 and line_2 are parallel, line_1, line_3 and line_4 are mutually orthogonal to each other. 
%                       2: line_1 and line_2 are parallel, line_3 and line_4 are parallel, line_1 is orthogonal to line_3. 
% Output: vanishingPoint -- [vaniX, vaniY, vaniZ]; at most two groups of possible results exist for four lines.
%                           vaniX: the vanishing point of lines which are parallel to X axis. 
%                           vaniY: the vanishing point of lines which are parallel to Y axis. 
%                           vaniZ: the vanishing point of lines which are parallel to Z axis. 
%         focal          -- the focal length of the camera, at most two groups of possible results exist for four lines.
%         numofResuluts  -- number of possible solutions, (0, 1, 2)
%The key idea is that the direction of lines in the camera frame is parameterized as
%  V1_c = [x1s - lambda_1 * x1e;  y1s - lambda_1 * y1e;  focal - lambda_1*focal];
%  V2_c = [x2s - lambda_2 * x2e;  y2s - lambda_2 * y2e;  focal - lambda_2*focal];
%  V3_c = [x3s - lambda_3 * x3e;  y3s - lambda_3 * y3e;  focal - lambda_3*focal];
%  V4_c = [x4s - lambda_4 * x4e;  y4s - lambda_4 * y4e;  focal - lambda_4*focal];
if size(lines,1) ~= 4
     error(' error in EstimateVPandFocalFrom4Lines(lines, configuration), only four lines are required.');
end

x1s = lines(1,2); y1s = lines(1,3); x1e = lines(1,4); y1e = lines(1,5); 
x2s = lines(2,2); y2s = lines(2,3); x2e = lines(2,4); y2e = lines(2,5); 
x3s = lines(3,2); y3s = lines(3,3); x3e = lines(3,4); y3e = lines(3,5); 
x4s = lines(4,2); y4s = lines(4,3); x4e = lines(4,4); y4e = lines(4,5); 

vanishingPoint = [];
focal          = [];

switch configuration
    case 1 %line_1 // line_2 /cdot line_3 /cdot line_4.
        % line_1 is parallel to line_2
        a0 =   x1s - x2s;
        a1 = -(x1e - x2s);
        a2 = -(x1s - x2e);
        a3 =   x1e - x2e;
        
        b0 =   y1s - y2s;
        b1 = -(y1e - y2s);
        b2 = -(y1s - y2e);
        b3 =   y1e - y2e;
        % f(lambda1) = w0 + w1 * lambda1 + w2 * lambda1^2;
        w0 = a2*b0 - a0*b2;
        w1 = a2*b1 + a3*b0 - a0*b3 - a1*b2;
        w2 = a3*b1 - a1*b3;
        % solve lambda1 from the 2 degree polynomial;
        temp1 = w1*w1-4*w2*w0;
        if temp1<-1e-5 %no real roots
            numofResuluts = 0;
            return; 
        end
        temp1 = real(sqrt(temp1));
        lambda1 = [(-w1+temp1); (-w1-temp1)]/(2*w2);
        % test whether the solution lambda1 = lambda2 = 1 is nontrival,
        % if imageLine1 is parallel to imageLine2 in the image plane, then
        % lambda1 = 1 is the double root of the quadratic equation.
        temp1 = abs(lambda1(1) - 1);
        temp2 = abs(lambda1(2) - 1);
        if  temp1>temp2
            lambda1 = lambda1(1);
        else
            lambda1 = lambda1(2);
        end
        %after solve lambda_1, according to line_1, line_3 and line_4 are orthogonal to
        %each other, we solve lambda_3, lambda_4 and focal. At most two real solutions
        a0 = x1s - lambda1 * x1e;
        a1 = y1s - lambda1 * y1e;
        a2 = 1   - lambda1;
        b0 = a0*x3s + a1*y3s;
        b1 = a0*x3e + a1*y3e;
        b2 = a0*x4s + a1*y4s;
        b3 = a0*x4e + a1*y4e;
        c0 = x3s*x4s+ y3s*y4s;
        c1 = x3e*x4s+ y3e*y4s;
        c2 = x3s*x4e+ y3s*y4e;
        c3 = x3e*x4e+ y3e*y4e;
        if abs(lambda1 - 1) <1.0e-5 %lambda1==1
            %solve lambda3 and lambda4 by using line1 \cdot line3 \cdot line4
            lambda3 = b0/b1;
            lambda4 = b2/b3;
            %test whether lambda3 or lambda4 equals to 1
            temp1 = abs(lambda3 - 1);
            temp2 = abs(lambda4 - 1);
            if temp1<1.0e-5 || temp2<1.0e-5
                numofResuluts = 0;
                return;
            end
            %otherwise, we solve the focal length from lambda3 and lambda4;
            temp1 = c0 - lambda3*c1  - lambda4*c2 + lambda3*lambda4*c3;
            temp2 = 1 - lambda3 - lambda4 + lambda3*lambda4;
            focal_square = -temp1/temp2;
            if focal_square<0
                numofResuluts = 0;
                return;
            end
            numofResuluts = 1;
            solution = [lambda1, lambda3, lambda4, sqrt(focal_square)];
        else %lambda1!=1
            % g(focal) = w0 + w1 * focal^2 + w2 * focal^4 = 0;
            w0 = c0*b1*b3 - c1*b0*b3 - c2*b2*b1 + c3*b0*b2;
            w1 = c0*a2*(b3+b1) - c1*a2*(b3+b0) - c2*a2*(b1+b2) + c3*a2*(b2+b0) + ...
                 b1*b3 - b0*b3 - b2*b1 + b0*b2;
            w2 = (c0 - c1 - c2 + c3)*a2*a2;
            % solve focal^2 from the polynomial;
            temp1 = w1*w1-4*w2*w0;
            if temp1<-1e-5 %no real roots
                numofResuluts = 0;
                return;
            end
            temp1 = real(sqrt(temp1));
            rs    = [(-w1+temp1); (-w1-temp1)]/(2*w2);
            % only keep the positive real roots because focal^2>0
            focal_square = rs(rs>0);
            numofResuluts = size(focal_square,1);
            if numofResuluts == 0
                return;
            end
            %according to the solution of lambda1 and focal, compute lambda3 and lambda4;
            solution = zeros(numofResuluts,4); % solution[i,:] = [lambda_1, lambda_3, lambda_4, focal]
            for focalID = 1: numofResuluts
                temp = focal_square(focalID) * a2;
                lambda3 = (temp+b0)/(temp+b1);
                lambda4 = (temp+b2)/(temp+b3);
                solution(focalID, :) = [lambda1, lambda3, lambda4, sqrt( focal_square(focalID) )];
            end
        end
        %compute the vanishing points;
        focal = solution(:,4);
        vanishingPoint = zeros(3, numofResuluts*3);
        for id = 1:numofResuluts
            tempVec = [x1s - solution(id,1) * x1e;  y1s - solution(id,1) * y1e;  focal(id)*(1 - solution(id,1))];
            vanishingPoint(:,id*3 - 2) =  tempVec/norm(tempVec); %vaniX = V1_c
            tempVec = [x3s - solution(id,2) * x3e;  y3s - solution(id,2) * y3e;  focal(id)*(1 - solution(id,2))];
            vanishingPoint(:,id*3 - 1) =  tempVec/norm(tempVec); %vaniY = V3_c
            tempVec = [x4s - solution(id,3) * x4e;  y4s - solution(id,3) * y4e;  focal(id)*(1 - solution(id,3))];
            vanishingPoint(:,id*3    ) =  tempVec/norm(tempVec); %vaniZ = V4_c
        end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    
    case 2 %line_1 // line_2 /cdot line_3 // line_4.
        % line_1 is parallel to line_2
        a0 =   x1s - x2s;
        a1 = -(x1e - x2s);
        a2 = -(x1s - x2e);
        a3 =   x1e - x2e;
        
        b0 =   y1s - y2s;
        b1 = -(y1e - y2s);
        b2 = -(y1s - y2e);
        b3 =   y1e - y2e;
        % f(lambda1) = w0 + w1 * lambda1 + w2 * lambda1^2;
        w0 = a2*b0 - a0*b2;
        w1 = a2*b1 + a3*b0 - a0*b3 - a1*b2;
        w2 = a3*b1 - a1*b3;
        % solve lambda1 from the 2 degree polynomial;
        temp1 = w1*w1-4*w2*w0;
        if temp1<-1e-5 %no real roots
            numofResuluts = 0;
            return;
        end
        temp1 = real(sqrt(temp1));
        lambda1 = [(-w1+temp1); (-w1-temp1)]/(2*w2);
        % test whether the solution lambda1 = lambda2 = 1 is nontrival,
        % if imageLine1 is parallel to imageLine2 in the image plane, then
        % lambda1 = 1 is the double root of the quadratic equation.
        temp1 = abs(lambda1(1) - 1);
        temp2 = abs(lambda1(2) - 1);
        if  temp1>temp2
            lambda1 = lambda1(1);
        else
            lambda1 = lambda1(2);
        end
        if abs(lambda1-1)<1e-5 % lambda1==1, the focal length is unsolvable.
            numofResuluts = 0;
            return;
        end
        % line_3 is parallel to line_4
        a0 =   x3s - x4s;
        a1 = -(x3e - x4s);
        a2 = -(x3s - x4e);
        a3 =   x3e - x4e;
        
        b0 =   y3s - y4s;
        b1 = -(y3e - y4s);
        b2 = -(y3s - y4e);
        b3 =   y3e - y4e;
        % f(lambda3) = w0 + w1 * lambda3 + w2 * lambda3^2;
        w0 = a2*b0 - a0*b2;
        w1 = a2*b1 + a3*b0 - a0*b3 - a1*b2;
        w2 = a3*b1 - a1*b3;
        % solve lambda3 from the 2 degree polynomial;
        temp1 = w1*w1-4*w2*w0;
        if temp1<-1e-5 %no real roots
            numofResuluts = 0;
            return;
        end
        temp1 = real(sqrt(temp1));
        lambda3 = [(-w1+temp1); (-w1-temp1)]/(2*w2);
        % test whether the solution lambda3 = lambda4 = 1 is nontrival,
        % if imageLine3 is parallel to imageLine4 in the image plane, then
        % lambda3 = 1 is the double root of the quadratic equation.
        temp1 = abs(lambda3(1) - 1);
        temp2 = abs(lambda3(2) - 1);
        if  temp1>temp2
            lambda3 = lambda3(1);
        else
            lambda3 = lambda3(2);
        end
        if abs(lambda3-1)<1e-5 % lambda3==1, the focal length is unsolvable.
            numofResuluts = 0;
            return;
        end
        % after solving lambda1 and lambda3, according to line_1 \cdot line_3,
        % we now compute the vanishing points and the focal length.
        temp1 = (x1s - lambda1*x1e)*(x3s-lambda3*x3e) + (y1s - lambda1*y1e)*(y3s-lambda3*y3e);
        temp2 = (1-lambda1)*(1-lambda3);
        focal_square = -temp1/temp2;
        if focal_square<0
            numofResuluts = 0;
            return;
        end
        numofResuluts = 1;
        focal = sqrt(focal_square);
        
        tempVec = [x1s - lambda1 * x1e;  y1s - lambda1 * y1e;  focal*(1 - lambda1)];
        vanishingPoint(:, 1) =  tempVec/norm(tempVec); %vaniX = V1_c = V2_c; Because they are parallel.
        tempVec = [x3s - lambda3 * x3e;  y3s - lambda3 * y3e;  focal*(1 - lambda3)];
        vanishingPoint(:, 2) =  tempVec/norm(tempVec); %vaniY = V3_c = V4_c;
        tempVec = cross( vanishingPoint(:, 1), vanishingPoint(:, 2) );
        vanishingPoint(:, 3) =  tempVec/norm(tempVec); %vaniZ = vaniX x vaniY;
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    
    otherwise
        error(' error in  EstimateVPandFocalFrom4Lines(lines, configuration), configuration must be either 1 or 2');
end

return