import { useState } from 'react';
import { useForm } from 'react-hook-form';
import Link from 'next/link';
import useProjectName from '../hooks/useProjectName';
import PageTitle from '../components/PageTitle';

type UnregisterFormData = {
  email: string;
  confirm: boolean;
};

export default function Unregister() {
  const projectName = useProjectName();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UnregisterFormData>();

  const onSubmit = async (data: UnregisterFormData) => {
    setIsSubmitting(true);
    setError('');
    
    try {
      const response = await fetch('/api/users/unregister', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: data.email,
          confirm: data.confirm,
        }),
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || 'Unregister request failed');
      }
      
      setIsSuccess(true);
    } catch (error) {
      setError(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-lg">
      <PageTitle title="Unregister" />
      
      <div className="bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold mb-6 text-center">
          Unregister from {projectName}
        </h1>
        
        {isSuccess ? (
          <div className="text-center">
            <div className="mb-4 text-green-500">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            
            <h2 className="text-xl font-semibold mb-4">Request Submitted</h2>
            
            <p className="mb-6">
              If your email is registered in our system, you will receive a confirmation 
              link to complete the unregistration process.
            </p>
            
            <p className="mb-6">
              Please check your email and follow the instructions to confirm 
              account deletion.
            </p>
            
            <Link href="/">
              <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
                Back to Home
              </span>
            </Link>
          </div>
        ) : (
          <>
            <p className="mb-6 text-gray-700">
              If you wish to unregister from the contest and delete all your data, 
              please fill in the form below.
            </p>
            
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}
            
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div>
                <label className="block mb-1">Your Email Address</label>
                <input
                  type="email"
                  {...register('email', { 
                    required: 'Email is required',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Invalid email address',
                    }
                  })}
                  className="w-full px-3 py-2 border rounded"
                />
                {errors.email && (
                  <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
                )}
              </div>
              
              <div className="flex items-start">
                <input
                  type="checkbox"
                  {...register('confirm', { 
                    required: 'You must confirm that you want to delete your account'
                  })}
                  className="mt-1 mr-2"
                />
                <div>
                  <label className="block">
                    I confirm that I want to delete my account and all associated data
                  </label>
                  {errors.confirm && (
                    <p className="text-red-500 text-sm mt-1">{errors.confirm.message}</p>
                  )}
                </div>
              </div>
              
              <div className="flex justify-between">
                <Link href="/">
                  <span className="inline-block text-blue-500 hover:underline">
                    Cancel
                  </span>
                </Link>
                
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-6 rounded focus:outline-none focus:shadow-outline"
                >
                  {isSubmitting ? 'Processing...' : 'Unregister'}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}