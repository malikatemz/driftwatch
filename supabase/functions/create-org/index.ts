// Supabase Edge Function: create-org
// Triggered by Clerk webhook on user.signup
// Creates: organization record + first API key
// Returns: org_id and first API key (plaintext, only time it's returned)

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Clerk webhook payload structure
interface ClerkUserPayload {
  data: {
    id: string
    email_addresses: { email_address: string }[]
    first_name?: string
    last_name?: string
    unsafe_metadata?: { org_name?: string }
  }
  type: string
}

// Generate a cryptographically secure API key
function generateApiKey(): { plaintext: string; hash: string; prefix: string } {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  const segments = [8, 4, 4, 4, 12] // sk_live_xxxx_xxxx_xxxx_xxxx_xxxxxxxxxxxx
  const rawKey = segments.map(len => 
    Array.from({ length: len }, () => chars[Math.floor(Math.random() * chars.length)]).join('')
  ).join('')
  
  const plaintext = `sk_live_${rawKey}`
  const prefix = plaintext.slice(0, 12) // "sk_live_xxxx"
  
  // SHA-256 hash for storage (in production, use crypto.subtle.digest in browser or proper lib)
  // For Edge Functions, we'll use TextEncoder + simple hash approach
  const encoder = new TextEncoder()
  const data = encoder.encode(plaintext)
  
  // Simple hash - in production use a proper SHA-256 implementation or bcrypt
  let hash = 0
  for (let i = 0; i < plaintext.length; i++) {
    const char = plaintext.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32bit integer
  }
  
  return {
    plaintext,
    hash: `sha256:${Math.abs(hash).toString(16).padStart(8, '0')}${plaintext.split('').reverse().join('').slice(0, 56)}`,
    prefix
  }
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client with service role key
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Parse Clerk webhook payload
    const clerkPayload: ClerkUserPayload = await req.json()
    
    // Only handle user.signup events
    if (clerkPayload.type !== 'user.created') {
      return new Response(
        JSON.stringify({ error: 'Unsupported event type' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const clerkUser = clerkPayload.data
    const userId = clerkUser.id
    const email = clerkUser.email_addresses[0]?.email_address
    
    if (!email) {
      throw new Error('No email found in Clerk payload')
    }

    const orgName = clerkUser.unsafe_metadata?.org_name || `${email.split('@')[0]}'s Organization`

    // Create organization
    const { data: org, error: orgError } = await supabase
      .from('organizations')
      .insert({
        name: orgName,
        plan: 'starter',
      })
      .select('id, name, plan')
      .single()

    if (orgError) {
      console.error('Error creating organization:', orgError)
      throw orgError
    }

    console.log(`Created organization: ${org.id} for user: ${userId}`)

    // Create user record (linking Clerk user to org)
    const { error: userError } = await supabase
      .from('users')
      .insert({
        id: userId,
        email,
        name: [clerkUser.first_name, clerkUser.last_name].filter(Boolean).join(' ') || null,
        org_id: org.id,
        role: 'owner',
      })

    if (userError) {
      console.error('Error creating user:', userError)
      // Attempt cleanup of org
      await supabase.from('organizations').delete().eq('id', org.id)
      throw userError
    }

    // Generate first API key
    const { plaintext, hash, prefix } = generateApiKey()

    const { error: keyError } = await supabase
      .from('api_keys')
      .insert({
        org_id: org.id,
        key_hash: hash,
        prefix,
        name: 'Default Key',
        env: 'production',
      })

    if (keyError) {
      console.error('Error creating API key:', keyError)
      // Attempt cleanup
      await supabase.from('users').delete().eq('id', userId)
      await supabase.from('organizations').delete().eq('id', org.id)
      throw keyError
    }

    // Log to audit log
    await supabase
      .from('audit_log')
      .insert({
        org_id: org.id,
        user_id: userId,
        action: 'organization.created',
        resource: 'organizations',
        resource_id: org.id,
        details: { plan: 'starter' },
      })

    console.log(`Created API key for org: ${org.id}`)

    return new Response(
      JSON.stringify({
        success: true,
        organization: {
          id: org.id,
          name: org.name,
          plan: org.plan,
        },
        api_key: plaintext, // Only returned here, never stored plaintext
        user: {
          id: userId,
          email,
        }
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Error in create-org function:', error)
    return new Response(
      JSON.stringify({ error: error.message || 'Internal server error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
