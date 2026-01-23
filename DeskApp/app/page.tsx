'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    const checkAuth = async () => {
      if (typeof window !== 'undefined' && (window as any).electronAPI) {
        const authStatus = await (window as any).electronAPI.checkAuth();
        if (authStatus.isAuthenticated) {
          router.push('/inbox');
        } else {
          router.push('/login');
        }
      } else {
        router.push('/login');
      }
    };
    
    checkAuth();
  }, [router]);
  
  return null;
}