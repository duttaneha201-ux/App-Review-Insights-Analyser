'use client';

import { useState } from 'react';
import SubscriptionForm from '@/components/SubscriptionForm';

export default function Home() {
  return (
    <div className="container">
      <h1>App Review Insights</h1>
      <p className="subtitle">
        Get weekly insights from your Google Play Store reviews
      </p>
      <SubscriptionForm />
    </div>
  );
}








