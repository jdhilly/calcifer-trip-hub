<script lang="ts">
	import { onMount } from 'svelte';
	import { PageHeader, Card, Button, IconBadge } from '@calcifer/ui';
	import { Calendar, ArrowRight, Check, X, Library } from '@lucide/svelte/icons';

	let { data } = $props();
	let trips = $state(data.trips);
	let online = $state(typeof navigator !== 'undefined' ? navigator.onLine : true);

	let upcoming = $derived.by(() => {
		const now = new Date();
		const inFourWeeks = new Date();
		inFourWeeks.setDate(inFourWeeks.getDate() + 30);
		const active = trips.filter(
			(t: any) => new Date(t.start_date) <= inFourWeeks && new Date(t.end_date) >= now
		);
		return active.length > 0 ? active[0] : (trips.length > 0 ? trips[0] : null);
	});

	let pastTrips = $derived(trips.filter((t: any) => new Date(t.end_date) < new Date()));
	let futureTrips = $derived(trips.filter((t: any) => new Date(t.end_date) >= new Date()));

	function formatDate(d: string): string {
		return new Date(d + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
	}

	function isOngoing(t: any): boolean {
		const now = new Date();
		return new Date(t.start_date) <= now && new Date(t.end_date) >= now;
	}

	function isPast(t: any): boolean {
		return new Date(t.end_date) < new Date();
	}

	function isFuture(t: any): boolean {
		return new Date(t.start_date) > new Date();
	}
</script>

<div class="mx-auto max-w-4xl px-4 py-6">
	{#if !online}
		<div class="mb-3 flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-400">
			<span class="h-2 w-2 rounded-full bg-amber-500"></span>
			Hors ligne — les données affichées sont celles de la dernière synchronisation
		</div>
	{/if}

	<PageHeader title="Voyages" description="Préparez vos valises et ne rien oublier" />

	{#if trips.length === 0}
		<Card variant="static" surface={40} padding="p-8" class="mt-6 text-center">
			<p class="text-coal-400">Aucun voyage pour l'instant.</p>
		</Card>
	{:else}
		{#if upcoming}
			<div class="mt-6">
				<h2 class="font-display text-xl text-ember-500">
					{isOngoing(upcoming) ? '🔄 En cours' : '⬆️ Prochain voyage'}
				</h2>
				<Card variant="interactive" href={`/${upcoming.id}`} padding="p-5" class="mt-2">
					<div class="flex items-center gap-3">
						<IconBadge size="md" interactive>
							<Calendar size={20} aria-hidden="true" />
						</IconBadge>
						<div class="flex-1">
							<h3 class="font-semibold text-coal-50">{upcoming.destination}</h3>
							<p class="text-sm text-coal-400">
								{formatDate(upcoming.start_date)}
								<ArrowRight size={14} class="inline" />
								{formatDate(upcoming.end_date)}
							</p>
						</div>
					</div>
				</Card>
			</div>
		{/if}

		<div class="mt-8">
			<h2 class="font-display text-lg text-coal-300">Tous les voyages</h2>
			<div class="mt-3 space-y-3">
				{#each trips as trip}
					<Card variant="interactive" href={`/${trip.id}`} padding="p-4">
						<div class="flex items-start gap-3">
							<div class="flex-1">
								<h3 class="font-semibold text-coal-50">{trip.destination}</h3>
								<p class="text-sm text-coal-400">
									{formatDate(trip.start_date)}
									<ArrowRight size={14} class="inline" />
									{formatDate(trip.end_date)}
								</p>
							</div>
							<div class="flex items-center gap-2 text-xs">
								{#if isOngoing(trip)}
									<span class="flex items-center gap-1 text-ember-500">
										<Check size={14} /> En cours
									</span>
								{:else if isFuture(trip)}
									<span class="flex items-center gap-1 text-ember-400">
										<Calendar size={14} /> À venir
									</span>
								{:else}
									<span class="flex items-center gap-1 text-coal-500">
										<X size={14} /> Terminé
									</span>
								{/if}
							</div>
						</div>
					</Card>
				{/each}
			</div>
		</div>
	{/if}
</div>
