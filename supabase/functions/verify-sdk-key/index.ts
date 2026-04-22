// Supabase Edge Function: verify-sdk-key
// Validates API key from SDK requests
// Returns org_id if valid, updates last_used_at
// Used by the SDK to authenticate incoming events

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Simple hash function matching create-org (should use proper SHA-256 in production)
function hashApiKey(plaintext: string): string {
  let hash = 0
  for (let i = 0; i < plaintext.length; i++) {
    const char = plaintext.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return `sha256:${Math.abs(hash).toString(16).padStart(8, '0')}${plaintext.split('').reverse().join('').slice(0, 56)}`
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Extract API key from Authorization header
    const authHeader = req.headers.get('Authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return new Response(
        JSON.stringify({ error: 'Missing or invalid Authorization header' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const apiKey = authHeader.slice(7) // Remove 'Bearer ' prefix
    
    if (!apiKey || !apiKey.startsWith('sk_live_') && !apiKey.startsWith('sk_test_')) {
      return new Response(
        JSON.stringify({ error: 'Invalid API key format' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Initialize Supabase with service role for key verification
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Extract prefix from the API key (first 12 chars: "sk_live_xxxx" or "sk_test_xxxx")
    const prefix = apiKey.slice(0, 12)

    // Find the API key by prefix (we don't store full key, only hash + prefix)
    // First, get all keys with matching prefix for this org
    const { data: keys, error: keyError } = await supabase
      .from('api_keys')
      .select('id, org_id, key_hash, prefix, env, expires_at, revoked_at')
      .eq('prefix', prefix)
      .is('revoked_at', null)

    if (keyError) {
      console.error('Error fetching API key:', keyError)
      throw keyError
    }

    if (!keys || keys.length === 0) {
      return new Response(
        JSON.stringify({ error: 'Invalid API key' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // For multiple keys with same prefix (unlikely but possible), check each
    // In production, you'd store a keyed hash (HMAC) for proper verification
    // Here we do a simple hash match
    const keyHash = hashApiKey(apiKey)
    const validKey = keys.find(k => k.key_hash === keyHash)

    if (!validKey) {
      return new Response(
        JSON.stringify({ error: 'Invalid API key' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Check if key is expired
    if (validKey.expires_at && new Date(validKey.expires_at) < new Date()) {
      return new Response(
        JSON.stringify({ error: 'API key has expired' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Update last_used_at (async, don't wait)
    supabase
      .from('api_keys')
      .update({ last_used_at: new Date().toISOString() })
      .eq('id', validKey.id)
      .then(({ error }) => {
        if (error) console.error('Failed to update last_used_at:', error)
      })

    // Log usage in audit log
    supabase
      .from('audit_log')
      .insert({
        org_id: validKey.org_id,
        action: 'api_key.used',
        resource: 'api_keys',
        resource_id: validKey.id,
        details: { env: validKey.env },
        ip_address: req.headers.get('x-forwarded-for') || null,
        user_agent: req.headers.get('user-agent') || null,
      })
      .then(({ error }) => {
        if (error) console.error('Failed to log audit:', error)
      })

    return new Response(
      JSON.stringify({
        valid: true,
        org_id: validKey.org_id,
        key_id: validKey.id,
        env: validKey.env,
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error in verify-sdk-key function:', error)
    return new Response(
      JSON.stringify({ error: error.message || 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
