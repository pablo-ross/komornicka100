import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta charSet="utf-8" />
        <meta name="theme-color" content="#2563EB" />
        <meta name="description" content="Komornicka 100 - Track your bike rides and compete with other riders" />
        <link rel="icon" href="/favicon.ico" />
        
        {/* Mobile specific meta tags */}
        <meta name="format-detection" content="telephone=no" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Komornicka 100" />
        
        {/* Preconnect to Strava */}
        <link rel="preconnect" href="https://www.strava.com" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}