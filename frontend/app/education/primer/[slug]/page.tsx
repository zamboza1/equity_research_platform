'use client';

import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '@/utils/api';
import { Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function PrimerPage() {
    const { slug } = useParams();
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!slug) return;

        api.get(`/education/primers/${slug}`)
            .then(res => {
                setContent(res.data.content);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setError('Failed to load primer content.');
                setLoading(false);
            });
    }, [slug]);

    if (loading) return (
        <div className="flex items-center justify-center h-screen">
            <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
        </div>
    );

    if (error) return (
        <div className="max-w-3xl mx-auto mt-10">
            <div className="p-4 bg-red-50 text-red-600 rounded-xl">
                {error}
            </div>
            <Link href="/education" className="mt-4 inline-block text-brand-600 font-medium">
                ← Back to Education
            </Link>
        </div>
    );

    return (
        <div className="max-w-4xl mx-auto bg-white p-8 rounded-2xl shadow-sm border border-slate-100 my-8">
            <Link href="/education" className="inline-flex items-center text-sm text-slate-500 hover:text-brand-600 transition-colors mb-6">
                <ArrowLeft className="w-4 h-4 mr-1" />
                Back to Knowledge Base
            </Link>

            <article className="prose prose-slate lg:prose-lg max-w-none prose-headings:text-slate-900 prose-headings:font-bold prose-a:text-brand-600 prose-strong:text-slate-900">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {content}
                </ReactMarkdown>
            </article>
        </div>
    );
}
