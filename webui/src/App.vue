<script setup lang="ts">
import { RouterView } from 'vue-router'
import { Toaster } from '@/components/ui/sonner'
</script>

<template>
  <Toaster position="top-center" :duration="2000" rich-colors />
  <RouterView />
</template>
