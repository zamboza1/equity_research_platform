'use client';

import Link from 'next/link';

const primers = [
    {
        slug: 'real_estate',
        title: 'REIT Modeling Primer',
        description: 'A plain-English guide to NAV, FFO, AFFO, and Cap Rates.',
        duration: '10 min read',
        level: 'Beginner'
    },

];

export default function EducationPage() {
    return (
        <div className="max-w-5xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold gradient-text">Knowledge Base</h1>
                <p className="text-slate-500 mt-2">Master the fundamentals of equity research across sectors.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {primers.map((primer) => (
                    <div key={primer.slug} className="group bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-all">
                        <div className="flex justify-between items-start mb-4">
                            <span className="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-medium">
                                {primer.level}
                            </span>
                        </div>

                        <h3 className="text-xl font-bold text-slate-900 mb-2">{primer.title}</h3>
                        <p className="text-slate-500 mb-6">{primer.description}</p>

                        <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-400">{primer.duration}</span>
                            <Link
                                href={`/education/primer/${primer.slug}`}
                                className="flex items-center text-sm font-semibold text-brand-600 hover:text-brand-700"
                            >
                                Start Learning
                            </Link>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
