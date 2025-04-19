// frontend/components/Meta.tsx
import Head from 'next/head';
import { useRouter } from 'next/router';
import useProjectName from '../hooks/useProjectName';

interface MetaProps {
  title?: string;
  description?: string;
  keywords?: string;
  canonical?: string;
}

const Meta: React.FC<MetaProps> = ({
  title,
  description = 'Track your bike rides and compete with other riders in the Komornicka 100 bike contest.',
  keywords = 'bike, cycling, contest, Strava, Komornicka',
  canonical,
}) => {
  const projectName = useProjectName();
  const router = useRouter();
  
  // Generate full title
  const fullTitle = title
    ? `${title} | ${projectName}`
    : projectName;
  
  // Generate canonical URL
  const baseUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || '';
  const canonicalUrl = canonical 
    ? canonical 
    : `${baseUrl}${router.asPath}`;

  return (
    <Head>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
      <meta charSet="utf-8" />
      
      {/* Favicon */}
      <link rel="icon" href="/favicon.ico" />
      
      {/* Open Graph / Social */}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:type" content="website" />
      
      {/* Twitter */}
      <meta name="twitter:card" content="summary" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      
      {/* Canonical URL */}
      <link rel="canonical" href={canonicalUrl} />
      
      {/* Mobile specific */}
      <meta name="format-detection" content="telephone=no" />
      <meta name="mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-status-bar-style" content="default" />
    </Head>
  );
};

export default Meta;