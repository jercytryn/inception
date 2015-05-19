function fig = plot_vanishing_points(I,lines,ids,v_pnt_n,fc,cc,alpha_c)

%plot line segments overlaid on the image and output the endpoints of the
%longest line segment
%
% $Id: plot_vanishing_points.m 1231 2012-01-07 00:39:07Z faraz $

if nargin > 5
    K(3,3) = 1;
    K(1,1) = fc(1);
    K(2,2) = fc(2);
    K(1,3) = cc(1);
    K(2,3) = cc(2);
    K(1,2) = alpha_c;
else
    K = fc;
end

fig = figure('Position', [750,500, 640,480]);
imshow(I,'Border','tight'), hold on

%colors = 'rbg';

% colors{1} = [.7 .7 1];
% colors{2} = [0 1 0];
% colors{3} = [1 1 0];
%colors{3} = [236 73 20]/236;

 colors{1} = [1 0 0];
 colors{2} = [0 1 0];
 colors{3} = [0 0 1];


% convert unit-norm vanishing points to projective vanishing points
v_pnt = zeros(2,3);
for k = 1:3
    tmp = K*v_pnt_n(:,k);
    v_pnt(:,k) = tmp(1:2)/tmp(3);
end

for k = 1:length(lines)
   dist1 = norm(lines(k,2:3) - v_pnt(:,ids(k))');
   dist2 = norm(lines(k,4:5) - v_pnt(:,ids(k))');
   
   if dist1 > dist2
       xy = [v_pnt(:,ids(k))'; lines(k,2:3)];
   else
       xy = [v_pnt(:,ids(k))'; lines(k,4:5)];
   end
   
%    plot(xy(:,1),xy(:,2),'LineWidth',3,'Color',colors(ids(k)));
   plot(xy(:,1),xy(:,2),'LineWidth',2,'Color',colors{ids(k)});

   % Plot beginnings and ends of lines
   %plot(xy(1,1),xy(1,2),'x','LineWidth',2,'Color','yellow');
   %plot(xy(2,1),xy(2,2),'x','LineWidth',2,'Color','red');

end

hold off