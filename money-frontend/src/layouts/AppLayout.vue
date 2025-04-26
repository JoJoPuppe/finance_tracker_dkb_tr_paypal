<template>
  <div class="h-screen flex flex-col overflow-hidden bg-gray-900 text-white">
    
    <!-- Main Content Container -->
    <div class="flex-1 bg-gray-100 w-full mx-auto flex flex-col overflow-hidden">
      <!-- Content Area -->
      <div class="flex-1 p-2 overflow-hidden">
          <slot name="rules"></slot>
      </div>
      
      <!-- Footer -->
      <footer class="flex-none text-center text-gray-400 p-2 text-sm">
        <p>© 2025 Money Money Money - Personal Finance Management</p>
      </footer>
    </div>
  </div>
</template>

<script>

export default {
  name: 'AppLayout',
};
</script>

<style scoped>
/* Any component-specific styles can go here */
</style>
