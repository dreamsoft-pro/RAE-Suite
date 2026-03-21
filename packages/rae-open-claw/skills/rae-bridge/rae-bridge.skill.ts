import { DefineSkill } from '@mariozechner/pi-agent-core';

export default DefineSkill({
  name: 'rae-bridge',
  description: 'Chief Orchestrator Bridge with Gemini Support. Analyzes RAE Modules with deep reasoning.',
  
  tools: {
    rae_bridge_audit: {
      description: 'Phase 3 Semantic Audit.',
      inputSchema: { type: 'object', properties: { prompt: { type: 'string' } }, required: ['prompt'] },
      async run({ prompt }) {
        const raeUrl = process.env.RAE_API_URL || 'http://rae-api-dev:8000';
        const response = await fetch(`${raeUrl}/v2/bridge/audit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt, source_agent: 'open-claw' })
        });
        return await response.json();
      }
    },
    
    rae_gemini_analyze: {
      description: 'Deep code analysis using Gemini Pro. Use for understanding complex RAE logic.',
      inputSchema: {
        type: 'object',
        properties: {
          code: { type: 'string' },
          module_name: { type: 'string' },
          tenant_id: { type: 'string' }
        },
        required: ['code', 'module_name', 'tenant_id']
      },
      async run({ code, module_name, tenant_id }) {
        const raeUrl = process.env.RAE_API_URL || 'http://rae-api-dev:8000';
        const response = await fetch(`${raeUrl}/v2/bridge/interact`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-Tenant-Id': tenant_id,
            'X-Project-Id': 'RAE-Deep-Audit'
          },
          body: JSON.stringify({
            intent: 'GEMINI_ANALYZE',
            source_agent: 'open-claw',
            target_agent: 'rae-oracle-gemini',
            payload: { module_name, code_snippet: code.substring(0, 10000) }
          })
        });
        return await response.json();
      }
    }
  }
});
