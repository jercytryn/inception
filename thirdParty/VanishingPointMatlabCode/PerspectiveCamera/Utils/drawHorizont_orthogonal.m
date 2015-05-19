function hor = drawHorizont_orthogonal(points_hor, points_ver, weights_hor, width, height, pp_imcoords)

    % default horizon
    angle_horizon = 0;

    horA = tan(angle_horizon);
    horC = height/2 - horA*width/2;               

    hor = [horA; -1; horC];
    hor = hor / norm(hor(1:2));
       
    
%     hold on;    
    
    if (~isempty(points_ver) && ~isempty(points_hor))

        points_hor_x = points_hor(:, 1);
        finite_pts = find(abs(points_hor_x - width/2) < width * 7);
        
        if (size(points_hor, 1) > length(finite_pts) && (size(points_hor, 1) ~= 0)) 
            
            points2(1:length (finite_pts), 1:2) = points_hor(finite_pts, 1:2);
            points_hor = points2;
            weights_hor = weights_hor(finite_pts);

        end;
        
        
        if (size (points_hor, 1) >= 1)
           
            projections = zeros(size(points_hor, 1), 2);    

            Ax = points_ver(1, 1); % x-coordinate of zenith
            Ay = points_ver(1, 2); % y-coordinate of zenith     

            Bx = pp_imcoords(1); % x-coordinate of principal point
            By = pp_imcoords(2); % y-coordinate of principal point

            for iHorPoint = 1:size(points_hor, 1)       

                Cx = points_hor(iHorPoint, 1); % x-coordinate of current vanishing point
                Cy = points_hor(iHorPoint, 2); % y-coordinate of current vanishing point

                LC = sqrt( (Bx-Ax)*(Bx-Ax) + (By-Ay)*(By-Ay) );
                rC = ( (Ay-Cy)*(Ay-By)-(Ax-Cx)*(Bx-Ax) ) / (LC*LC);

                PCx = Ax + rC*(Bx-Ax); % x-coordinate of projecton of vanishing point on AB
                PCy = Ay + rC*(By-Ay); % y-coordinate of projecton of vanishing point on AB

                projections(iHorPoint, 1) = PCx;
                projections(iHorPoint, 2) = PCy;     
               
            end;

            mean_projection_x = sum(projections(:, 1).*weights_hor) / sum(weights_hor);
            mean_projection_y = sum(projections(:, 2).*weights_hor) / sum(weights_hor);
          
            angle_zenith_pp = atan2(Ay-By, Ax-Bx);
            angle_horizon = angle_zenith_pp + pi/2;

            horA = tan(angle_horizon);
            horC = mean_projection_y - horA*mean_projection_x;               

            hor = [horA; -1; horC];
            hor = hor / norm(hor(1:2));

        end
    end;

% x = 1;
% p1 = [x; (-hor(1)*x - hor(3)) / hor(2); 1];
% x = width;
% p2 = [x; (-hor(1)*x - hor(3)) / hor(2); 1];
% 
% hold on;
% plot([p1(1) p2(1)], [p1(2) p2(2)], 'Color', hor_color, 'LineWidth', 7);
                







