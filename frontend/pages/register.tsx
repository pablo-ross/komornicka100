import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useRouter } from 'next/router';
import Link from 'next/link';
import useProjectName from '../hooks/useProjectName';
import PageTitle from '../components/PageTitle';

type FormData = {
  firstName: string;
  lastName: string;
  age: number;
  email: string;
  termsAccepted: boolean;
  dataProcessingAccepted: boolean;
};

export default function Register() {
  const projectName = useProjectName();
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true);
    setSubmitError('');
    
    try {
      const response = await fetch('/api/users/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: data.firstName,
          last_name: data.lastName,
          age: data.age,
          email: data.email,
          terms_accepted: data.termsAccepted,
          data_processing_accepted: data.dataProcessingAccepted,
        }),
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || 'Registration failed');
      }
      
      // On success, redirect to success page
      router.push('/registration-success');
    } catch (error) {
      setSubmitError(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-lg">
      <PageTitle title="Register" />
      
      <h1 className="text-2xl font-bold mb-8 text-center">
        Register for {projectName}
      </h1>
      
      {submitError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {submitError}
        </div>
      )}
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <label className="block mb-1">First Name</label>
          <input
            type="text"
            {...register('firstName', { required: 'First name is required' })}
            className="w-full px-3 py-2 border rounded"
          />
          {errors.firstName && (
            <p className="text-red-500 text-sm mt-1">{errors.firstName.message}</p>
          )}
        </div>
        
        <div>
          <label className="block mb-1">Last Name</label>
          <input
            type="text"
            {...register('lastName', { required: 'Last name is required' })}
            className="w-full px-3 py-2 border rounded"
          />
          {errors.lastName && (
            <p className="text-red-500 text-sm mt-1">{errors.lastName.message}</p>
          )}
        </div>
        
        <div>
          <label className="block mb-1">Age</label>
          <input
            type="number"
            {...register('age', { 
              required: 'Age is required',
              min: { value: 18, message: 'You must be at least 18 years old' },
              valueAsNumber: true,
            })}
            className="w-full px-3 py-2 border rounded"
          />
          {errors.age && (
            <p className="text-red-500 text-sm mt-1">{errors.age.message}</p>
          )}
        </div>
        
        <div>
          <label className="block mb-1">Email</label>
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
            {...register('termsAccepted', { 
              required: 'You must accept the terms and regulations'
            })}
            className="mt-1 mr-2"
          />
          <div>
            <label className="block">
              I have read the <Link href="/terms" className="text-blue-500 underline">
                terms and regulations
              </Link> and I agree to follow these regulations
            </label>
            {errors.termsAccepted && (
              <p className="text-red-500 text-sm mt-1">{errors.termsAccepted.message}</p>
            )}
          </div>
        </div>
        
        <div className="flex items-start">
          <input
            type="checkbox"
            {...register('dataProcessingAccepted', { 
              required: 'You must accept the data processing agreement'
            })}
            className="mt-1 mr-2"
          />
          <div>
            <label className="block">
              I agree to the processing of my personal data by the contest organizer in order to participate in this contest
            </label>
            {errors.dataProcessingAccepted && (
              <p className="text-red-500 text-sm mt-1">{errors.dataProcessingAccepted.message}</p>
            )}
          </div>
        </div>
        
        <div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          >
            {isSubmitting ? 'Registering...' : 'Register'}
          </button>
        </div>
        
        <div className="text-center">
          <Link href="/unregister" className="text-blue-500">
            Unregister from contest
          </Link>
        </div>
      </form>
    </div>
  );
}