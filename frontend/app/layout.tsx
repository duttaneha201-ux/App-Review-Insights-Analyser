import './globals.css';

export const metadata = {
  title: 'App Review Insights Analyzer',
  description: 'Get weekly insights from your app reviews',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}








