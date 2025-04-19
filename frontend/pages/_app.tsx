import { AppProps } from 'next/app';
import { useEffect, useState } from 'react';
import '../styles/globals.css';
import useProjectName from '../hooks/useProjectName';
import Meta from '../components/Meta';

function MyApp({ Component, pageProps }: AppProps) {
  const projectName = useProjectName();
  const [mounted, setMounted] = useState(false);
  
  // Effect for client-side only code
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <>
      <Meta title={pageProps.title} />
      
      <div className="min-h-screen flex flex-col">
        <header className="bg-blue-600 text-white py-4">
          <div className="container mx-auto px-4">
            <a href="/" className="text-xl font-bold">{mounted ? projectName : 'Komornicka 100'}</a>
          </div>
        </header>
        
        <main className="flex-grow py-8">
          <Component {...pageProps} />
        </main>
        
        <footer className="bg-gray-100 py-6">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="mb-4 md:mb-0">
                <p className="text-gray-600 text-sm">
                  &copy; {new Date().getFullYear()} {mounted ? projectName : 'Komornicka 100'}
                </p>
              </div>
              <div className="flex space-x-4">
                <a href="/" className="text-gray-600 hover:text-blue-500 text-sm">Home</a>
                <a href="/terms" className="text-gray-600 hover:text-blue-500 text-sm">Terms</a>
                <a href="/register" className="text-gray-600 hover:text-blue-500 text-sm">Register</a>
                <a href="/unregister" className="text-gray-600 hover:text-blue-500 text-sm">Unregister</a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}

export default MyApp;