import React, { useState } from 'react';
import { Search, Info, ExternalLink, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { mockRules } from '../data/mockRules';

function RuleCard({ rule }) {
  const [expanded, setExpanded] = useState(false);

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'MANDATORY': return <Badge variant="danger">MANDATORY</Badge>;
      case 'CONDITIONAL': return <Badge variant="warning">CONDITIONAL</Badge>;
      case 'RECOMMENDED': return <Badge variant="success">RECOMMENDED</Badge>;
      default: return <Badge>{severity}</Badge>;
    }
  };

  const reference = rule.ruleRef || rule.reference || rule.id;
  const description = rule.description || rule.fullDescription || rule.shortDescription || '';
  const exemptions = Array.isArray(rule.exemptions) 
    ? rule.exemptions 
    : rule.exemptions 
      ? [rule.exemptions] 
      : [];
  const examples = Array.isArray(rule.examples) 
    ? rule.examples 
    : rule.examples 
      ? [rule.examples] 
      : [];

  return (
    <Card 
      className="overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="p-5 flex flex-col h-full">
        <div className="flex justify-between items-start mb-3 gap-2">
          <Badge variant="primary" className="bg-blue-50 text-blue-700">
            {rule.category}
          </Badge>
          {getSeverityBadge(rule.severity)}
        </div>
        
        <h3 className="text-lg font-semibold text-gray-900 mb-1">{rule.name}</h3>
        <div className="font-mono text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded inline-block mb-3 w-fit">
          {reference}
        </div>
        
        <p className={`text-sm text-gray-600 ${!expanded && 'line-clamp-2'} mb-4 flex-grow`}>
          {description}
        </p>

        <div className="text-xs text-gray-400 flex items-center justify-between mt-auto">
          <span>Effective: {rule.effectiveDate} (v{rule.version})</span>
          <span className="flex items-center text-blue-600 font-medium">
            {expanded ? (
              <><ChevronUp className="w-4 h-4 mr-1" /> Less</>
            ) : (
              <><ChevronDown className="w-4 h-4 mr-1" /> Details</>
            )}
          </span>
        </div>

        {expanded && (
          <div className="mt-4 pt-4 border-t border-gray-100 space-y-4" onClick={(e) => e.stopPropagation()}>
            <div>
              <h4 className="text-sm font-semibold text-gray-800 mb-1">Full Requirement</h4>
              <p className="text-sm text-gray-600">{description}</p>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold text-gray-800 mb-1">Applicability</h4>
              <p className="text-sm text-gray-600">{rule.applicability}</p>
            </div>
            
            {rule.exemptions && rule.exemptions.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-800 mb-1">Exemptions</h4>
                <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                  {rule.exemptions.map((ex, i) => <li key={i}>{ex}</li>)}
                </ul>
              </div>
            )}
            
            {rule.examples && rule.examples.length > 0 && (
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
                <h4 className="text-sm font-semibold text-gray-800 mb-2">Examples</h4>
                <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                  {rule.examples.map((ex, i) => <li key={i}>{ex}</li>)}
                </ul>
              </div>
            )}
            
            <div className="pt-2">
              <Button variant="outline" size="sm" className="w-full">
                <ExternalLink className="w-3 h-3 mr-2" /> View Official Notification
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

export default function RulesPage() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');

  const categories = ['All', 'Mandatory Declarations', 'Quantity Declaration', 'Pricing', 'Date Marking', 'Consumer Protection', 'Import Rules'];

  const filteredRules = mockRules.filter(rule => {
    if (category !== 'All' && rule.category !== category) return false;
    if (search) {
      const q = search.toLowerCase();
      return rule.name.toLowerCase().includes(q) || 
             rule.reference.toLowerCase().includes(q) || 
             rule.shortDescription.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="p-4 lg:p-6 max-w-7xl mx-auto space-y-6 pb-12">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold text-gray-900">Rule Engine - Legal Metrology Reference</h1>
        <div className="bg-blue-50 text-blue-800 text-sm p-3 rounded-lg flex items-start gap-2 border border-blue-100">
          <Info className="w-5 h-5 shrink-0 mt-0.5" />
          <p>
            <span className="font-semibold">Important Note:</span> Rule applicability depends on product type, package type, jurisdiction, and current applicable legal requirements. This is a reference tool only and does not substitute official legal interpretation.
          </p>
        </div>
      </div>

      <Card>
        <CardContent className="p-4 flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search rules, keywords, or references..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="w-4 h-4" />}
            />
          </div>
          <div className="w-full md:w-64 shrink-0">
            <select
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 outline-none h-[42px]"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredRules.length > 0 ? (
          filteredRules.map(rule => (
            <RuleCard key={rule.id} rule={rule} />
          ))
        ) : (
          <div className="col-span-full py-12 text-center text-gray-500">
            No rules found matching your search criteria.
          </div>
        )}
      </div>
      
      <div className="mt-8 bg-yellow-50 p-4 rounded-lg border border-yellow-200 flex items-start gap-3">
        <Info className="w-5 h-5 text-yellow-600 mt-0.5 shrink-0" />
        <p className="text-sm text-yellow-800">
          This rule reference is for enforcement guidance only. Officers should consult the latest published official gazettes for final determination. AI analysis maps extracted data to these rules using fuzzy matching and confidence scores.
        </p>
      </div>
    </div>
  );
}
