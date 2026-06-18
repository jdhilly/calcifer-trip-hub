<script lang="ts">
	import { PageHeader, Button, IconBadge } from '@calcifer/ui';
	import { Sparkles } from '@lucide/svelte/icons';

	let { data } = $props();
	let trip = $derived(data.trip);
	let artifacts = $state(data.artifacts);
	let generating = $state<string | null>(null);
	let online = $state(typeof navigator !== 'undefined' ? navigator.onLine : true);

	const types: Record<string, { icon: string; label: string }> = {
		'slide-deck': { icon: '📽️', label: 'Slide-deck' },
		audio: { icon: '🎧', label: 'Podcast' },
		infographic: { icon: '📊', label: 'Infographie' },
		flashcards: { icon: '🃏', label: 'Flashcards' }
	};

	function ico(t: string) {
		const m: Record<string, string> = { pdf: '📄', report: '📊', 'slide-deck': '📽️', video: '🎬', audio: '🎧', infographic: '📊', 'mind-map': '🧠', flashcards: '🃏', podcast: '🎙️' };
		return m[t] ?? '📄';
	}

	async function gen(type: string) {
		generating = type;
		try {
			const r = await fetch('/' + trip.id + '/briefing?/generate', {
				method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
				body: new URLSearchParams({ type })
			});
			const result = await r.json();
			if (result.ok) window.location.reload(); else alert('Erreur: ' + (result.error || 'Inconnue'));
		} catch (e: any) { alert('Erreur réseau: ' + e.message); }
		finally { generating = null; }
	}
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader title="Briefing" backHref={`/${trip.id}`} description={trip.destination} />

	<div class="mb-6 rounded-2xl border border-coal-800 bg-coal-900/55 p-5">
		<div class="flex items-center gap-3 mb-4">
			<IconBadge size="md"><Sparkles size={20} /></IconBadge>
			<div class="flex-1">
				<h3 class="font-semibold text-coal-50">Génération NotebookLM</h3>
				<p class="text-xs text-coal-400">{online ? 'Clique pour générer un briefing' : 'Indisponible hors ligne'}</p>
			</div>
		</div>
		{#if !online}<div class="mb-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-400">📡 Hors ligne</div>{/if}
		<div class="flex flex-wrap gap-2">
			{#each Object.entries(types) as [type, meta]}
				<button disabled={!online || generating !== null} onclick={() => gen(type)}
					class="inline-flex items-center gap-1.5 rounded-lg border border-coal-700 bg-coal-900 px-3 py-1.5 text-xs text-coal-300 transition-colors hover:border-ember-500 hover:text-ember-400 disabled:opacity-40">
					{generating === type ? '⏳' : meta.icon} {generating === type ? 'Génération...' : meta.label}
				</button>
			{/each}
		</div>
	</div>

	<h2 class="mb-3 font-display text-lg text-coal-300">Artificats existants</h2>

	{#if artifacts.length > 0}
		<div class="space-y-3">
			{#each artifacts as a}
				<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-4">
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-3">
							<span class="text-xl">{ico(a.type)}</span>
							<div>
								<p class="text-sm text-coal-100">{a.title || a.type}</p>
								<p class="text-xs text-coal-500">
									{new Date(a.created_at).toLocaleDateString('fr-FR')}
									{#if a.status === 'stale'} • <span class="text-amber-500">À régénérer</span>{/if}
									{#if a.status === 'generating'} • <span class="text-ember-400">En cours...</span>{/if}
								</p>
							</div>
						</div>
						{#if a.file_path}<a href={a.file_path} target="_blank"
							class="rounded-lg border border-coal-700 bg-coal-900 px-3 py-1.5 text-xs text-coal-300 hover:border-ember-500 hover:text-ember-400">Télécharger</a>{/if}
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<div class="rounded-2xl border border-coal-800 bg-coal-900/55 p-8 text-center"><p class="text-coal-500">Aucun artifact.</p></div>
	{/if}
</div>
