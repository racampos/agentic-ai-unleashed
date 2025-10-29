import type { LabMetadata } from '../../types';

interface LabCardProps {
  lab: LabMetadata;
  onSelect: (labId: string) => void;
}

const DIFFICULTY_COLORS = {
  beginner: 'bg-green-500/20 text-green-300 border-green-500/30',
  intermediate: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  advanced: 'bg-red-500/20 text-red-300 border-red-500/30',
};

export function LabCard({ lab, onSelect }: LabCardProps) {
  return (
    <div
      onClick={() => onSelect(lab.id)}
      className="group bg-gray-800 border border-gray-700 rounded-lg p-6 hover:border-blue-500 hover:bg-gray-750 transition-all cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-xl font-semibold text-white group-hover:text-blue-400 transition-colors">
          {lab.title}
        </h3>
        <div
          className={`px-2 py-1 rounded text-xs font-medium border ${
            DIFFICULTY_COLORS[lab.difficulty]
          }`}
        >
          {lab.difficulty}
        </div>
      </div>

      {/* Description */}
      <p className="text-gray-400 text-sm mb-4 line-clamp-2">
        {lab.description}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span className="flex items-center">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {lab.estimated_time} min
        </span>

        {lab.prerequisites.length > 0 && (
          <span className="flex items-center">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {lab.prerequisites.length} prereq{lab.prerequisites.length > 1 ? 's' : ''}
          </span>
        )}
      </div>
    </div>
  );
}
