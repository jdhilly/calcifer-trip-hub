<script lang="ts">
	import { PageHeader, Card, Button, IconBadge } from '@calcifer/ui';
	import { Plus, X, BookOpen } from '@lucide/svelte/icons';

	let { data } = $props();
	let trip = $derived(data.trip);
	let entries = $state(data.entries);
	let showForm = $state(false);
	let newContent = $state('');
	let newDate = $state(new Date().toISOString().slice(0, 10));
	let newAuthor = $state('');

	async function addEntry() {
		if (!newContent.trim()) return;
		const r = await fetch('/' + trip.id + '/journal?/add', {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ content: newContent.trim(), date: newDate, author: newAuthor.trim() })
		});
		const result = await r.json();
		if (result.ok) window.location.reload();
	}

	async function delEntry(id: number) {
		if (!confirm('Supprimer cette entrée ?')) return;
		const r = await fetch('/' + trip.id + '/journal?/delete', {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: new URLSearchParams({ entryId: String(id) })
		});
		const result = await r.json();
		if (result.ok) entries = entries.filter((e: any) => e.id !== id);
	}

	function fmtDate(d: string) { return new Date(d + 'T12:00:00').toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }); }
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	<PageHeader title="Journal de bord" backHref={`/${trip.id}`} description={trip.destination} />

	<div class="mb-6">
		<button onclick={() => (showForm = !showForm)}
			class="inline-flex items-center gap-1.5 rounded-lg border border-coal-700 bg-coal-900 px-3 py-1.5 text-xs text-coal-300 transition-colors hover:border-ember-500 hover:text-ember-400">
			<Plus size={14} /> {showForm ? 'Annuler' : 'Nouvelle entrée'}
		</button>
	</div>

	{#if showForm}
		<Card variant="static" surface={40} padding="p-4" class="mb-6">
			<div class="mb-3 flex flex-wrap gap-2">
				<input type="date" bind:value={newDate}
					class="rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none focus:border-ember-500" />
				<input bind:value={newAuthor} placeholder="Auteur"
					class="min-w-[150px] flex-1 rounded-lg border border-coal-700 bg-coal-900 px-3 py-2 text-sm text-coal-50 outline-none placeholder:text-coal-400 focus:border-ember-500" />
			</div>
			<textarea bind:value={newContent} placeholder="Que s'est-il passé aujourd'hui ?"
				class="mb-3 w-full rounded-lg border border-coal-700 bg-coal-900 p-3 text-sm text-coal-50 outline-none placeholder:text-coal-400 focus:border-ember-500" rows="4"></textarea>
			<Button onclick={addEntry} disabled={!newContent.trim()}>Publier</Button>
		</Card>
	{/if}

	{#if entries.length > 0}
		<div class="mt-6 space-y-4">
			{#each entries as entry (entry.id)}
				<Card variant="static" surface={40} padding="p-4" reveal>
					<div class="mb-2 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<span class="font-display text-base text-coal-50">{fmtDate(entry.date)}</span>
							{#if entry.author}
								<span class="rounded bg-coal-800 px-2 py-0.5 text-xs text-coal-400">{entry.author}</span>
							{/if}
						</div>
						<button onclick={() => delEntry(entry.id)} class="text-coal-600 hover:text-red-400 transition-colors" title="Supprimer"><X size={14} /></button>
					</div>
					<p class="whitespace-pre-wrap text-sm leading-relaxed text-coal-200">{entry.content}</p>
				</Card>
			{/each}
		</div>
	{:else}
		<Card variant="static" surface={40} padding="p-8" class="mt-6 text-center">
			<p class="text-coal-500">Aucune entrée pour ce voyage.</p>
		</Card>
	{/if}
</div>
