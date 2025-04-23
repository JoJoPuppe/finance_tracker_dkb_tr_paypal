<template>
  <div class="p-2 transition-colors duration-200">
    <div class="flex items-center justify-between">
      <!-- Category Content -->
      <div class="flex items-center">
        <!-- Expand/Collapse button if has subcategories -->
        <button 
          v-if="hasSubcategories" 
          @click="$emit('toggle-expand')" 
          class="text-gray-600 w-6 h-6 cursor-pointer flex items-center justify-center mr-2 rounded-full focus:outline-none"
          title="Expand/Collapse"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transition-transform" :class="{ 'rotate-90': category.isExpanded !== false }" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
          </svg>
        </button>
        
        <!-- Placeholder for categories without subcategories -->
        <div v-else class="w-6 mr-2"></div>
        
        <div>
          <!-- Category name with badge if it's a parent -->
          <div class="flex items-center">
            <span class="text-lg font-medium" :class="{ 'text-gray-600': !category.parent_id, 'text-white': category.parent_id }">
              {{ category.name }}
            </span>
          </div>
          
          <!-- Parent info for subcategories -->
          <p v-if="category.parent_id" class="text-xs text-gray-400 mt-0.5">
            Subcategory
          </p>
        </div>
      </div>
      
      <!-- Actions -->
      <div class="flex space-x-2">
        <button
          @click="$emit('edit', category)"
          class="text-gray-400 hover:text-gray-600 transition-colors p-1 focus:outline-none"
          title="Edit Category"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
          </svg>
        </button>
        <button
          @click="$emit('delete', category.id)"
          class="text-gray-400 hover:text-gray-600 transition-colors p-1 focus:outline-none"
          title="Delete Category"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CategoryItem',
  props: {
    category: {
      type: Object,
      required: true
    }
  },
  computed: {
    hasSubcategories() {
      return this.category.subcategories && this.category.subcategories.length > 0;
    }
  }
}
</script>

<style scoped>
/* Using Tailwind classes, but we can add custom styles here if needed */
</style>
