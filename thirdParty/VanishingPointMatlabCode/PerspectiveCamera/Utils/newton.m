function [x, err]=newton(fun, dfun, x0, TOL, DAMPED, nmax, numeric) 
 
 % Implementation of the well known Newton method.
 % 
 % INPUT:  fun     the function to investigate, given as inline function
 %         dfun    the derivative, given as inline function
 %         x0      starting guess
 %         TOL     tolerance for declaration of convergence
 %         DAMPED  = 0 for the standard undamped method
 %                 = 1 for the damped method to achieve global
 %                 convergence
 %         nmax    maximum number of iteration steps
 %         numeric use numerical differentiation
 %
 % OUTPUT: Table giving the iterates and corresponding function values
 %         Plot visualizing the iteration steps
 % Author: B. Flemisch
 
 %clf;
 small = 1e-8;
 sigma = 0.0001; % parameter for damped method
 rho = 0.5; % parameter for damped method
 

 x = x0;
 err = abs(feval(fun, x0)); 
 
 nit = 0; 
 while((nit < nmax) & (err > TOL))
   nit = nit + 1; 
   if (numeric)
     dx = max(sqrt(eps)*abs(x), 1e-8); % step width for central difference
     dfx = (feval(fun, x + dx) - feval(fun, x - dx))/(2*dx);
   else
     dfx = feval(dfun,x); % get derivative
   end
 
   if (abs(dfx) < small) % zero derivative -> divergence of the method
     break;
   else
     d = - feval(fun,x)/dfx; % get search direction
     alpha = 1.0; % damping parameter set to 1
     xold = x;
     x = x + alpha*d; % new iterate
     if (DAMPED),
       f2 = feval(fun,xold).^2;
       f2n = feval(fun,x).^2;
       while (f2n > f2 + sigma*alpha*feval(fun,xold)*d) 
         alpha = rho*alpha; % damping parameter is adjusted
         x = xold + alpha*d; % adjust iterate
         f2n = feval(fun,x).^2;
       end
     end
     err = abs(feval(fun, x));
   end
 end
 