<template>
  <div>
    <TransitionGroup name="list" tag="ul" class="space-y-3">
      <li v-for="category in processedCategories" :key="category.id" class="fade-in">
        <div class="overflow-hidden">
          <CategoryItem 
            :category="category"
            @edit="$emit('edit', category)"
            @delete="$emit('delete', category.id)"
            @toggle-expand="toggleExpand(category)"
          />
          
          <Transition name="slide">
            <div 
              v-if="category.isExpanded !== false && category.subcategories && category.subcategories.length > 0"
              class="pl-4 ml-2 mt-1 border-l-2 border-gray-800"
            >
              <CategoryList
                :categories="category.subcategories"
                @edit="$emit('edit', $event)"
                @delete="$emit('delete', $event)"
              />
            </div>
          </Transition>
        </div>
      </li>
    </TransitionGroup>
  </div>
</template>

<script>
import { computed, watch, reactive } from 'vue';
import CategoryItem from './CategoryItem.vue';

export default {
  name: 'CategoryList',
  components: {
    CategoryItem,
  },
  props: {
    categories: {
      type: Array,
      required: true,
    },
  },
  emits: ['edit', 'delete'],
  setup(props) {
    // Process categories to add expandability state
    const processedCategories = reactive([]);
    
    // Function to update processed categories when props change
    const updateProcessedCategories = () => {
      processedCategories.splice(0, processedCategories.length); // Clear current array
      props.categories.forEach(cat => {
        processedCategories.push({
          ...cat,
          isExpanded: true // Default to expanded
        });
      });
    };
    
    // Initialize processed categories
    updateProcessedCategories();
    
    // Watch for changes in the categories prop
    watch(() => props.categories, () => {
      updateProcessedCategories();
    }, { deep: true });

    const toggleExpand = (category) => {
      category.isExpanded = !category.isExpanded;
    };

    return {
      processedCategories,
      toggleExpand
    };
  }
};
</script>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 1000px;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}

.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
