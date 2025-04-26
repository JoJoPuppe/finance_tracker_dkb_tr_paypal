<template>
  <div class="h-screen w-full overflow-hidden">
    <AppLayout :initial-active-tab="currentView" @refresh="handleRefresh">
      <template #categories>
        <CategoryEditor />
      </template>
      <template #rules>
        <RulesEditor />
      </template>
    </AppLayout>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import AppLayout from './layouts/AppLayout.vue';
import CategoryEditor from './components/CategoryEditor.vue';
import RulesEditor from './components/RulesEditor.vue';
import Transactions from './components/Transactions.vue';

export default {
  name: 'App',
  components: {
    AppLayout,
    CategoryEditor,
    RulesEditor,
    Transactions
  },
  setup() {
    const currentView = ref('categories');
    const categories = ref([]);
    const refreshKey = ref(0); // Add refresh key to force component refresh
    
    // Fetch categories for use in the Transactions component
    const fetchCategories = async () => {
      try {
        const response = await axios.get('/api/v1/categories');
        if (response.data.status === 'success') {
          categories.value = response.data.data;
        }
      } catch (error) {
        console.error('Failed to fetch categories:', error);
      }
    };
    
    // Handle refresh event from AppLayout
    const handleRefresh = () => {
      fetchCategories();
      refreshKey.value++; // Increment to force re-render of components
    };
    
    // Fetch categories when the component is mounted
    onMounted(fetchCategories);
    
    return {
      currentView,
      categories,
      refreshKey,
      handleRefresh
    };
  }
};
</script>

<style>
/* Add global styles here if needed */
</style>
