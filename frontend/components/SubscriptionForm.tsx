'use client';

import { useState } from 'react';

interface FormData {
  playstoreUrl: string;
  weeks: number;
  email: string;
}

interface FormErrors {
  playstoreUrl?: string;
  weeks?: string;
  email?: string;
  submit?: string;
}

export default function SubscriptionForm() {
  const [formData, setFormData] = useState<FormData>({
    playstoreUrl: '',
    weeks: 4,
    email: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Frontend validations
  const validatePlayStoreUrl = (url: string): string | undefined => {
    if (!url.trim()) {
      return 'Play Store URL is required';
    }
    const playStorePattern =
      /^https?:\/\/(play\.google\.com\/store\/apps\/details\?id=|apps\.android\.com\/details\?id=)[a-zA-Z0-9._-]+/;
    if (!playStorePattern.test(url)) {
      return 'Please enter a valid Google Play Store app URL';
    }
    return undefined;
  };

  const validateEmail = (email: string): string | undefined => {
    if (!email.trim()) {
      return 'Email is required';
    }
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
      return 'Please enter a valid email address';
    }
    return undefined;
  };

  const validateWeeks = (weeks: number): string | undefined => {
    if (weeks < 1 || weeks > 12) {
      return 'Week range must be between 1 and 12';
    }
    return undefined;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSuccess(false);

    // Frontend validation
    const newErrors: FormErrors = {};
    const urlError = validatePlayStoreUrl(formData.playstoreUrl);
    const emailError = validateEmail(formData.email);
    const weeksError = validateWeeks(formData.weeks);

    if (urlError) newErrors.playstoreUrl = urlError;
    if (emailError) newErrors.email = emailError;
    if (weeksError) newErrors.weeks = weeksError;

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/subscriptions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          playstore_url: formData.playstoreUrl,
          weeks: formData.weeks,
          email: formData.email,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle different error types
        let errorMessage = 'Something went wrong. Please try again later.';

        if (response.status === 400) {
          if (data.error?.includes('does not exist')) {
            errorMessage = 'This app does not exist on Play Store.';
          } else if (data.error?.includes('No reviews')) {
            errorMessage = 'No reviews found for the selected time range.';
          } else if (data.error?.includes('email')) {
            errorMessage = 'Please enter a valid email address.';
          } else {
            errorMessage = data.error || errorMessage;
          }
        } else if (response.status === 404) {
          errorMessage = 'This app does not exist on Play Store.';
        }

        setErrors({ submit: errorMessage });
        setIsSubmitting(false);
        return;
      }

      // Success
      setSuccess(true);
      setSuccessMessage(
        data.message ||
          'Analysis started. You will receive the insights by email.'
      );
      setIsSubmitting(false);

      // Reset form after 3 seconds
      setTimeout(() => {
        setFormData({
          playstoreUrl: '',
          weeks: 4,
          email: '',
        });
        setSuccess(false);
      }, 5000);
    } catch (error: any) {
      console.error('Submission error:', error);
      // Check if it's a network/connection error
      let errorMessage = 'Something went wrong. Please try again later.';
      if (error instanceof TypeError && error.message?.includes('fetch')) {
        errorMessage = 'Cannot connect to server. Please make sure the backend API is running on http://localhost:8000';
      } else if (error.message && (error.message.includes('Failed to fetch') || error.message.includes('NetworkError'))) {
        errorMessage = 'Connection failed. Please check that the backend server is running.';
      }
      setErrors({
        submit: errorMessage,
      });
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Play Store URL Input */}
      <div className="form-group">
        <label htmlFor="playstoreUrl">
          Google Play Store App URL <span style={{ color: '#e53e3e' }}>*</span>
        </label>
        <input
          type="text"
          id="playstoreUrl"
          value={formData.playstoreUrl}
          onChange={(e) =>
            setFormData({ ...formData, playstoreUrl: e.target.value })
          }
          placeholder="https://play.google.com/store/apps/details?id=com.example.app"
          className={errors.playstoreUrl ? 'error' : ''}
          disabled={isSubmitting}
        />
        {errors.playstoreUrl && (
          <div className="error-message">⚠️ {errors.playstoreUrl}</div>
        )}
        <div className="help-text">
          Enter the full URL of your app from Google Play Store
        </div>
      </div>

      {/* Week Range Selector */}
      <div className="form-group">
        <label htmlFor="weeks">
          Week Range <span style={{ color: '#e53e3e' }}>*</span>
        </label>
        <div className="week-selector">
          <input
            type="range"
            id="weeks"
            min="1"
            max="12"
            value={formData.weeks}
            onChange={(e) =>
              setFormData({ ...formData, weeks: parseInt(e.target.value) })
            }
            disabled={isSubmitting}
          />
          <div className="week-value">{formData.weeks} weeks</div>
        </div>
        {errors.weeks && (
          <div className="error-message">⚠️ {errors.weeks}</div>
        )}
        <div className="help-text">
          Select how many weeks of reviews to analyze (reviews from last 7 days
          are excluded)
        </div>
      </div>

      {/* Email Input */}
      <div className="form-group">
        <label htmlFor="email">
          Email Address <span style={{ color: '#e53e3e' }}>*</span>
        </label>
        <input
          type="email"
          id="email"
          value={formData.email}
          onChange={(e) =>
            setFormData({ ...formData, email: e.target.value })
          }
          placeholder="your.email@example.com"
          className={errors.email ? 'error' : ''}
          disabled={isSubmitting}
        />
        {errors.email && (
          <div className="error-message">⚠️ {errors.email}</div>
        )}
        <div className="help-text">
          You will receive weekly insights at this email address
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        className="submit-button"
        disabled={isSubmitting}
      >
        {isSubmitting ? (
          <span className="loading">
            <div className="spinner"></div>
            Processing...
          </span>
        ) : (
          'Start Analysis'
        )}
      </button>

      {/* Error Message */}
      {errors.submit && (
        <div className="error-message" style={{ marginTop: '16px' }}>
          ⚠️ {errors.submit}
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="success-message">
          <strong>✓ Success!</strong>
          <div style={{ marginTop: '8px' }}>{successMessage}</div>
        </div>
      )}
    </form>
  );
}







