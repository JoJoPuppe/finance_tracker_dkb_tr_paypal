<template>
  <div class="h-screen flex flex-col overflow-hidden">

    <!-- Main Layout: Side Panels and Content -->
    <div class="flex flex-col md:flex-row gap-x-2 h-full overflow-hidden">
      <!-- Side Panel with Rules List -->
      <div class="">
        <div class="w-1/4 flex gap-x-3 h-10">
          <!-- Select User dropdown placeholder (commented out for now) -->
          <!-- <select class="bg-gray-700 text-white px-3 py-2 rounded border border-gray-600">
            <option>Select User</option>
          </select> -->
          <select 
            v-model="selectedUserId" 
            class="border border-black px-3 py-2 text-black bg-white cursor-pointer"
          >
            <option value="" disabled>Select User</option>
            <option v-for="user in users" :key="user.id" :value="user.id">
              {{ user.name }}
            </option>
          </select>
          
          <label class="relative cursor-pointer border border-black bg-white hover:bg-gray-600 hover:text-white hover:border-gray-600 text-black px-4 py-2 transition-colors duration-300 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a 1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
            </svg>
            <span class="mr-2">CSV</span>
            <input 
              type="file" 
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
              accept=".csv"
              @change="handleFileUpload"
              :disabled="!selectedUserId"
            />
          </label>

          <!-- Create User Button -->
          <button 
            @click="openUserModal" 
            class="bg-blue-600 cursor-pointer hover:bg-blue-700 text-white px-4 py-2 flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            User
          </button>
          
          <!-- Create Category Button -->
          <button 
            @click="handleCreateCategory" 
            class="bg-green-600 cursor-pointer hover:bg-green-700 text-white px-4 py-2 flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Category
          </button>
          
          <!-- Create Rule Button -->
          <button 
            @click="handleCreateRule" 
            class="bg-purple-600 cursor-pointer hover:bg-purple-700 text-white px-4 py-2 flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Rule
          </button>

          <div 
            v-if="showToast" 
            class="fixed top-5 right-5 p-4 rounded-md shadow-lg transition-all duration-500"
            :class="{ 
              'bg-green-500': toastType === 'success',
              'bg-red-500': toastType === 'error'
            }"
          >
            {{ toastMessage }}
          </div>
      </div>

      <div class="w-1/4 flex pt-6">
        <div class="">
          <h2 class="text-xl font-bold text-gray-600 mb-2">Rules</h2>
          <div class="border-r border-r-black py-4 overflow-auto h-[calc(100vh-130px)]">
            <rule-list
              ref="ruleListComponent"
              :categories="categories"
              @select-rule="handleRuleSelect"
              @edit-rule="handleEditRule"
              @delete-rule="handleDeleteRule"
              @revert-rule="handleRevertRule"
            />
          </div>
        </div>

        <!-- Side Panel with Categories List -->
        <div class="">
          <h2 class="text-xl font-bold text-gray-600 mb-2">Categories</h2>
          <div class="border-r border-r-black p-1 overflow-auto h-[calc(100vh-130px)]">
            <category-list
              :categories="rootCategories"
              @edit="editCategory"
              @delete="confirmDeleteCategory"
            />
          </div>
        </div>
        </div>
      </div>
      
      <!-- Main Content Area -->
      <div class="flex-1 flex flex-col overflow-hidden pl-4">
        <!-- Rule Application Results -->
        <div v-if="ruleApplyResult" class="bg-green-900 bg-opacity-30 border border-green-600 rounded-lg p-4 mb-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-500 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <p class="text-green-300">{{ ruleApplyResult }}</p>
            </div>
            <button 
              @click="hideRuleResult" 
              class="text-green-400 hover:text-green-200 transition-colors"
              aria-label="Close"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Loading indicator for rule application -->
        <div v-if="applyingRule" class="bg-purple-900 bg-opacity-20 border border-purple-600 rounded-lg p-4 mb-4 flex items-center">
          <svg class="animate-spin h-5 w-5 text-purple-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-purple-300">Applying rule to transactions...</p>
        </div>
    
        <!-- Record Preview -->
        <record-preview 
          :record="recordPreview" 
          :highlight-key="searchColumn"
        />
    
     

        <!-- Transactions by Category Section -->
        <div class="flex-1 overflow-hidden">
          <transactions 
            :categories="categories"
            :refresh-trigger="refreshTrigger"
          />
        </div>
      </div>
    </div>

    <!-- Toast notifications -->
    <Toast 
      :message="toast.message" 
      :type="toast.type" 
      :is-visible="toast.isVisible" 
    />
    
    <!-- Category Modal -->
    <Modal 
      :is-open="showCategoryModal" 
      :title="categoryFormMode === 'create' ? 'Create Category' : 'Update Category'"
      @close="showCategoryModal = false"
      @update:isOpen="showCategoryModal = $event"
    >
      <category-form
        :parent-categories="availableParents"
        :initial-data="categoryFormData"
        :is-edit-mode="categoryFormMode === 'edit'"
        :has-subcategories="categoryFormMode === 'edit' && hasSubcategories(categoryFormData.id)"
        @submit="handleCategorySubmit"
        @close="closeCategoryModal"
      />
    </Modal>

    <!-- Rule Modal -->
    <Modal 
      :is-open="showRuleModal" 
      :title="currentEditRule ? 'Update Rule' : 'Create Rule'"
      size="large"
      @close="closeRuleModal"
      @update:isOpen="showRuleModal = $event"
    >
      <rule-form
        :available-columns="availableColumns"
        :categories="categories"
        :edit-rule="currentEditRule"
        @rule-created="handleRuleCreated"
        @rule-updated="handleRuleUpdated"
        @cancel-edit="closeRuleModal"
        @error="handleRuleError"
      />
    </Modal>

    <!-- User Modal -->
    <Modal 
      :is-open="showUserModal" 
      title="Manage Users"
      @close="closeUserModal"
      @update:isOpen="showUserModal = $event"
    >
      <user-form
        :users="users"
        @submit-success="handleUserSubmit"
        @close="closeUserModal"
        @error="handleUserError"
      />
    </Modal>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue';
import axios from 'axios';

// Import modular components
import RuleSearch from './RuleSearch.vue';
import RecordPreview from './RecordPreview.vue';
import RuleForm from './RuleForm.vue';
import RuleList from './RuleList.vue';
import CategoryList from './CategoryList.vue';
import CategoryForm from './CategoryForm.vue';
import UserForm from './UserForm.vue'; // Import the new UserForm component
import Toast from './Toast.vue';
import Transactions from './Transactions.vue';
import Modal from './Modal.vue';

export default {
  name: 'RulesEditor',
  components: { 
    RuleSearch,
    RecordPreview,
    RuleForm,
    RuleList,
    CategoryList,
    CategoryForm,
    UserForm, // Add the UserForm component
    Toast,
    Transactions,
    Modal
  },
  
  setup() {
    const toastMessage = ref('');
    const toastType = ref('success');

    // Rule state variables
    const availableColumns = ref([]);
    const searchColumn = ref('');
    const recordPreview = ref(null);
    const categories = ref([]);
    const currentEditRule = ref(null);
    const ruleApplyResult = ref(null);
    const applyingRule = ref(false);
    const refreshTrigger = ref(0);
    const ruleListComponent = ref(null); // Reference to the rule list component

    // User selection and CSV upload functionality
    const users = ref([]);
    const selectedUserId = ref('');
    
    // Category state variables
    const categoryFormMode = ref('create');
    const categoryFormData = ref({ name: '', parentId: null });
    const showCategoryModal = ref(false);
    const showRuleModal = ref(false);
    
    // Toast notification
    const toast = reactive({
      isVisible: false,
      message: '',
      type: 'success'
    });
    
    // Computed
    const rootCategories = computed(() => {
      return categories.value.filter(category => !category.parent_id);
    });

    const availableParents = computed(() => {
      // Filter to only include top-level categories
      const topLevelCategories = categories.value.filter(cat => !cat.parent_id);
      
      if (categoryFormMode.value === 'edit') {
        // When editing, exclude the current category from parent options
        const currentCategoryId = categoryFormData.value.id;
        return topLevelCategories.filter(cat => {
          // Don't allow a category to be its own parent or child of its children
          return cat.id !== currentCategoryId && !isDescendantOf(cat.id, currentCategoryId);
        });
      }
      return topLevelCategories;
    });

    // Fetch initial data when component mounts
    onMounted(async () => {
      await Promise.all([fetchColumns(), fetchCategories(), fetchUsers()]);
    });

    const fetchUsers = async () => {
      try {
        const response = await axios.get('/api/v1/users');
        if (response.data && response.data.status === 'success') {
          users.value = response.data.data;
        }
      } catch (error) {
        console.error('Error fetching users:', error);
        showToast('Error loading users. Please refresh the page.', 'error');
      }
    }


    const handleFileUpload = async (event) => {
      const file = event.target.files[0];
      if (!file) return;
      
      // Check if user is selected
      if (!selectedUserId.value) {
        showToast('Please select a user first', 'error');
        return;
      }
      
      // Check if file is a CSV
      if (!file.name.endsWith('.csv')) {
        showToast('Please select a CSV file', 'error');
        return;
      }
      
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', selectedUserId.value);
      
      try {
        // Show loading toast
        showToast('Uploading file...', 'success');
        
        // Send to backend using axios instead of fetch
        const response = await axios.post('/api/v1/transactions/import', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        // Display success message
        showToast(response.data.message || 'CSV file imported successfully');
        
        // Reset file input
        event.target.value = '';
        
        // Trigger refresh of parent component
        emit('refresh');
        
        // Refresh the page (optional)
        setTimeout(() => {
          window.location.reload();
        }, 1000);
        
      } catch (error) {
        console.error('Error uploading CSV:', error);
        const errorMessage = error.response?.data?.message || error.message || 'Error uploading file';
        displayToast(errorMessage, 'error');
        
        // Reset file input
        event.target.value = '';
      }
    };

    
    // Fetch column data
    const fetchColumns = async () => {
      try {
        const response = await axios.get('/api/v1/transactions/columns');
        if (response.data.status === 'success') {
          availableColumns.value = response.data.data.columns;
        } else {
          showToast('Failed to load column data', 'error');
        }
      } catch (error) {
        console.error('Error fetching columns:', error);
        showToast('Failed to load column data', 'error');
      }
    };
    
    // Fetch categories data
    const fetchCategories = async () => {
      try {
        const response = await axios.get('/api/v1/categories');
        if (response.data.status === 'success') {
          categories.value = response.data.data;
          organizeCategories();
        } else {
          showToast('Failed to load categories', 'error');
        }
      } catch (error) {
        console.error('Error fetching categories:', error);
        showToast('Failed to load categories', 'error');
      }
    };

    const organizeCategories = () => {
      // This method ensures each category has a subcategories array
      categories.value.forEach(category => {
        if (!category.subcategories) {
          category.subcategories = [];
        }
      });
    };

    // Category Management Methods
    const isDescendantOf = (categoryId, potentialAncestorId) => {
      const category = categories.value.find(c => c.id === categoryId);
      if (!category) return false;
      
      if (category.parent_id === potentialAncestorId) return true;
      if (category.parent_id) {
        return isDescendantOf(category.parent_id, potentialAncestorId);
      }
      return false;
    };

    const hasSubcategories = (categoryId) => {
      const category = categories.value.find(c => c.id === categoryId);
      return category && category.subcategories && category.subcategories.length > 0;
    };

    const resetCategoryForm = () => {
      categoryFormMode.value = 'create';
      categoryFormData.value = { name: '', parentId: null };
    };

    const editCategory = (category) => {
      categoryFormMode.value = 'edit';
      categoryFormData.value = { 
        id: category.id,
        name: category.name,
        parentId: category.parent_id
      };
      showCategoryModal.value = true; // Show the modal when editing
    };

    const createCategory = async (categoryData) => {
      try {
        const response = await axios.post('/api/v1/categories', {
          name: categoryData.name,
          parent_id: categoryData.parentId || null
        });
        
        if (response.data.status === 'success') {
          showToast('Category created successfully', 'success');
          await fetchCategories(); // Refresh the list
          resetCategoryForm();
        } else {
          showToast('Failed to create category', 'error');
        }
      } catch (err) {
        console.error('Error creating category:', err);
        showToast(
          err.response?.data?.message || 'Failed to create category', 
          'error'
        );
      }
    };

    const updateCategory = async (categoryData) => {
      try {
        const response = await axios.put(`/api/v1/categories/${categoryData.id}`, {
          name: categoryData.name,
          parent_id: categoryData.parentId || null
        });
        
        if (response.data.status === 'success') {
          showToast('Category updated successfully', 'success');
          await fetchCategories(); // Refresh the list
          resetCategoryForm();
        } else {
          showToast('Failed to update category', 'error');
        }
      } catch (err) {
        console.error('Error updating category:', err);
        showToast(
          err.response?.data?.message || 'Failed to update category', 
          'error'
        );
      }
    };

    const confirmDeleteCategory = (categoryId) => {
      if (confirm('Are you sure you want to delete this category? This action cannot be undone.')) {
        deleteCategory(categoryId);
      }
    };

    const deleteCategory = async (categoryId) => {
      try {
        const response = await axios.delete(`/api/v1/categories/${categoryId}`);
        
        if (response.data.status === 'success') {
          categories.value = categories.value.filter(cat => cat.id !== categoryId);
          showToast('Category deleted successfully', 'success');
        } else {
          showToast('Failed to delete category', 'error');
        }
      } catch (err) {
        console.error('Error deleting category:', err);
        const errorMessage = err.response?.data?.message || 'Failed to delete category';
        showToast(errorMessage, 'error');
      }
    };
    
    // Fetch methods
    // Method to refresh the rules list
    const fetchRules = async () => {
      if (ruleListComponent.value) {
        await ruleListComponent.value.refreshRules();
      }
    };
    
    // Apply a rule to all transactions
    const applyRule = async (ruleId) => {
      applyingRule.value = true;
      ruleApplyResult.value = null;
      
      try {
        const response = await axios.post(`/api/v1/transactions/apply-rule/${ruleId}`);
        if (response.data.status === 'success') {
          ruleApplyResult.value = response.data.message;
          showToast(response.data.message, 'success');
          refreshTrigger.value++;
          await fetchRules(); // Refresh the rules list
        } else {
          showToast('Failed to apply rule to transactions', 'error');
        }
      } catch (error) {
        console.error('Error applying rule:', error);
        showToast(error.response?.data?.message || 'Failed to apply rule to transactions', 'error');
      } finally {
        applyingRule.value = false;
      }
    };

    // Revert a rule's effects on all transactions
    const revertRule = async (ruleId) => {
      applyingRule.value = true;
      ruleApplyResult.value = null;
      
      try {
        const response = await axios.post(`/api/v1/transactions/revert-rule/${ruleId}`);
        if (response.data.status === 'success') {
          ruleApplyResult.value = response.data.message;
          showToast(response.data.message, 'success');
          refreshTrigger.value++;
          await fetchRules(); // Refresh the rules list
        } else {
          showToast('Failed to revert rule effects on transactions', 'error');
        }
      } catch (error) {
        console.error('Error reverting rule:', error);
        showToast(error.response?.data?.message || 'Failed to revert rule effects on transactions', 'error');
      } finally {
        applyingRule.value = false;
      }
    };
    
    // Handle rule selection from the side panel
    const handleRuleSelect = (rule) => {
      console.log('Selected rule:', rule);
    };
    
    // Handle rule edit request
    const handleEditRule = (rule) => {
      currentEditRule.value = rule;
      showRuleModal.value = true;
      showToast('Editing rule: ' + rule.name, 'info');
    };
    
    // Cancel editing
    const cancelEdit = () => {
      currentEditRule.value = null;
    };
    
    // Handle rule deletion
    const handleDeleteRule = (ruleId, errorMessage = null) => {
      if (errorMessage) {
        showToast(errorMessage, 'error');
      } else {
        showToast('Rule deleted successfully', 'success');
        if (currentEditRule.value && currentEditRule.value.id === ruleId) {
          currentEditRule.value = null;
        }
      }
    };

    // Handle rule revert
    const handleRevertRule = (ruleId) => {
      revertRule(ruleId);
    };
    
    // Handle search result from RuleSearch component
    const handleSearchResult = (result) => {
      recordPreview.value = result;
    };
    
    // Handle search error from RuleSearch component
    const handleSearchError = (error) => {
      showToast(error, 'error');
    };
    
    // Handle successful rule creation
    const handleRuleCreated = (rule) => {
      showToast('Rule created successfully', 'success');
      // Reset any current edit state
      currentEditRule.value = null;
      // Close the modal
      showRuleModal.value = false;
      applyRule(rule.id);
    };
    
    // Handle successful rule update
    const handleRuleUpdated = (rule) => {
      showToast('Rule updated successfully', 'success');
      currentEditRule.value = null;
      // Close the modal
      showRuleModal.value = false;
      applyRule(rule.id);
    };
    
    // Handle rule creation/update error
    const handleRuleError = (error) => {
      showToast(error, 'error');
    };
    
    // Display toast notification
    const showToast = (message, type = 'success') => {
      toast.message = message;
      toast.type = type;
      toast.isVisible = true;
      setTimeout(() => (toast.isVisible = false), 8000);
    };

    // Handle Create Category button click
    const handleCreateCategory = () => {
      resetCategoryForm();
      categoryFormMode.value = 'create';
      showCategoryModal.value = true;
    };
    
    // Handle category form submission from modal
    const handleCategorySubmit = (categoryData) => {
      if (categoryFormMode.value === 'create') {
        createCategory(categoryData);
      } else {
        updateCategory(categoryData);
      }
    };
    
    // Close the category modal
    const closeCategoryModal = () => {
      showCategoryModal.value = false;
    };

    // Handle Create Rule button click
    const handleCreateRule = () => {
      currentEditRule.value = null;
      showRuleModal.value = true;
    };

    // Close the rule modal
    const closeRuleModal = () => {
      showRuleModal.value = false;
    };

    // Hide rule result
    const hideRuleResult = () => {
      ruleApplyResult.value = null;
    };

    // User-related state
    const showUserModal = ref(false);
    
    // User modal functions
    const openUserModal = () => {
      fetchUsers();
      showUserModal.value = true;
    };
    
    const closeUserModal = () => {
      showUserModal.value = false;
    };
    
    const handleUserSubmit = (result) => {
      let message;
      
      if (result.type === 'create') {
        message = `User ${result.user.name} created successfully`;
        users.value.push(result.user);
      } else if (result.type === 'update') {
        message = `User ${result.user.name} updated successfully`;
        const index = users.value.findIndex(user => user.id === result.user.id);
        if (index !== -1) {
          users.value[index] = result.user;
        }
      } else if (result.type === 'delete') {
        message = 'User deleted successfully';
        users.value = users.value.filter(user => user.id !== result.userId);
      } else if (result.type === 'create-bank-account') {
        message = `Bank account "${result.bankAccount.name}" created successfully`;
      } else if (result.type === 'update-bank-account') {
        message = `Bank account "${result.bankAccount.name}" updated successfully`;
      } else if (result.type === 'delete-bank-account') {
        message = 'Bank account deleted successfully';
      }
      
      toast.message = message;
      toast.type = 'success';
      toast.isVisible = true;
      
      // Auto-hide the toast after 5 seconds
      setTimeout(() => {
        toast.isVisible = false;
      }, 5000);
      
      // Only close the modal for user operations, not bank account operations
      if (['create', 'update', 'delete'].includes(result.type)) {
        closeUserModal();
      }
    };
    
    const handleUserError = (errorMessage) => {
      toast.message = errorMessage;
      toast.type = 'error';
      toast.isVisible = true;
    };
    
    return {
      // Rule data
      availableColumns,
      searchColumn,
      recordPreview,
      currentEditRule,
      ruleApplyResult,
      applyingRule,
      refreshTrigger,
      ruleListComponent,
      
      // User data
      users,
      selectedUserId,
      handleFileUpload,
      
      // Category data
      categories,
      rootCategories,
      categoryFormMode,
      categoryFormData,
      availableParents,
      showCategoryModal,
      showRuleModal,
      
      // Toast
      toast,
      
      // Rule methods
      handleRuleSelect,
      handleEditRule,
      handleDeleteRule,
      handleRevertRule,
      handleSearchResult,
      handleSearchError,
      handleRuleCreated,
      handleRuleUpdated,
      handleRuleError,
      cancelEdit,
      
      // Category methods
      editCategory,
      createCategory,
      updateCategory,
      confirmDeleteCategory,
      deleteCategory,
      hasSubcategories,
      resetCategoryForm,
      
      // Common methods
      showToast,

      // Header button methods
      handleCreateCategory,
      handleCreateRule,
      handleCategorySubmit,
      closeCategoryModal,
      closeRuleModal,
      hideRuleResult,

      // User-related
      showUserModal,
      openUserModal,
      closeUserModal,
      handleUserSubmit,
      handleUserError
    };
  }
};
</script>

<style scoped>
.loader {
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: #9f7aea;
}
</style>
