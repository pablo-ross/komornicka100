import Head from 'next/head';
import useProjectName from '../hooks/useProjectName';

type PageTitleProps = {
  title: string;
};

export default function PageTitle({ title }: PageTitleProps) {
  const projectName = useProjectName();
  const fullTitle = `${title} | ${projectName}`;
  
  return (
    <Head>
      <title>{fullTitle}</title>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <link rel="icon" href="/favicon.ico" />
    </Head>
  );
}