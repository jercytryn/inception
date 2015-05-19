%ROTVEC Rotation about arbitrary axis
%
% 	TR = axisAndangle2rot(V, THETA)
%
% Returns a homogeneous transformation representing a rotation of THETA 
% about the vector V.
%
% See also: ROTX, ROTY, ROTZ.

% Copyright (C) 1993-2002, by Peter I. Corke


function r = axisAndangle2rot(v, t)

	v = v/norm(v);
	ct = cos(t);
	st = sin(t);
	vt = 1-ct;
	v = v(:);
	r =    [ct		-v(3)*st	v(2)*st
		v(3)*st		ct		-v(1)*st
		-v(2)*st	v(1)*st		ct	];
	r = v*v'*vt+r;
    
