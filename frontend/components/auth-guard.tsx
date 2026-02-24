'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';
import { Loader2 } from 'lucide-react';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    // Check auth on mount and path change
    const checkAuth = () => {
      const isAuth = isAuthenticated();
      const isPublicPath = pathname === '/login'; // Add other public paths here

      if (!isAuth && !isPublicPath) {
        setAuthorized(false);
        router.push('/login');
      } else if (isAuth && isPublicPath) {
        setAuthorized(true); 
        router.push('/'); // Redirect logged in users away from login
      } else {
        setAuthorized(true);
      }
    };

    checkAuth();
  }, [pathname, router]);

  // Optionally show a loading state while checking
  // For now, we render children but if redirected, the router will handle it.
  // To avoid flash of content, we can show a loader until authorized is true
  // ONLY for protected routes.
  
  const isPublicPath = pathname === '/login';
  
  if (!authorized && !isPublicPath) {
     return (
        <div className="flex h-full items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-navy-900" />
        </div>
     );
  }

  return <>{children}</>;
}
