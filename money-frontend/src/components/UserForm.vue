<template>
  <div class="bg-gray-700 rounded-lg p-5">
    <form @submit.prevent="submitForm" class="space-y-6">
      <!-- User Selection -->
      <div class="mb-4" v-if="users.length > 0">
        <label class="block text-gray-300 mb-2">Select User</label>
        <select 
          v-model="selectedUserId" 
          class="w-full bg-gray-800 text-white border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:border-purple-500"
          @change="handleUserSelect"
        >
          <option value="">-- Create New User --</option>
          <option v-for="user in users" :key="user.id" :value="user.id">
            {{ user.name }} ({{ user.email }})
          </option>
        </select>
      </div>
      
      <!-- Name Input -->
      <div class="mb-4">
        <label class="block text-gray-300 mb-2">Name *</label>
        <input 
          type="text" 
          v-model="formData.name" 
          class="w-full bg-gray-800 text-white border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:border-purple-500"
          placeholder="Enter user name"
          :class="{ 'border-red-500': validationErrors.name }"
        >
        <p v-if="validationErrors.name" class="text-red-500 text-sm mt-1">{{ validationErrors.name }}</p>
      </div>
      
      <!-- Email Input -->
      <div class="mb-4">
        <label class="block text-gray-300 mb-2">Email *</label>
        <input 
          type="email" 
          v-model="formData.email" 
          class="w-full bg-gray-800 text-white border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:border-purple-500"
          placeholder="Enter email address"
          :class="{ 'border-red-500': validationErrors.email }"
        >
        <p v-if="validationErrors.email" class="text-red-500 text-sm mt-1">{{ validationErrors.email }}</p>
      </div>
      
      <!-- Action Buttons -->
      <div class="flex justify-between">
        <button 
          type="button" 
          @click="$emit('close')" 
          class="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded-md transition duration-200"
        >
          Cancel
        </button>
        
        <div class="flex space-x-3">
          <button 
            v-if="isEditMode"
            type="button"
            @click="confirmDeleteUser"
            class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md transition duration-200"
            :disabled="isSubmitting"
          >
            Delete
          </button>
          
          <button 
            type="submit"
            class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-md transition duration-200 flex items-center"
            :disabled="isSubmitting"
          >
            <span v-if="isSubmitting" class="mr-2">
              <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </span>
            {{ isEditMode ? 'Update User' : 'Create User' }}
          </button>
        </div>
      </div>
    </form>

    <!-- Bank Accounts Section - Only show when editing a user -->
    <div v-if="isEditMode" class="mt-8 pt-6 border-t border-gray-600">
      <h3 class="text-xl text-white font-semibold mb-4">Bank Accounts</h3>
      
      <!-- List of existing bank accounts -->
      <div v-if="bankAccounts.length > 0" class="mb-6">
        <div class="bg-gray-800 rounded-md overflow-hidden">
          <div class="grid grid-cols-12 text-gray-300 text-sm bg-gray-750 p-3">
            <div class="col-span-3">Name</div>
            <div class="col-span-6">IBAN</div>
            <div class="col-span-3 text-right">Actions</div>
          </div>
          
          <div v-for="account in bankAccounts" :key="account.id" class="grid grid-cols-12 p-3 text-white border-t border-gray-700">
            <div class="col-span-3 truncate" :title="account.name">{{ account.name }}</div>
            <div class="col-span-6 truncate" :title="account.iban">{{ account.iban }}</div>
            <div class="col-span-3 text-right space-x-2">
              <button 
                @click="editBankAccount(account)"
                class="text-blue-400 hover:text-blue-300"
                title="Edit"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button 
                @click="confirmDeleteBankAccount(account)"
                class="text-red-400 hover:text-red-300"
                title="Delete"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="text-gray-400 italic mb-6">No bank accounts found for this user.</div>

      <!-- Bank Account Form -->
      <div class="bg-gray-750 rounded-md p-4">
        <h4 class="text-lg text-white font-medium mb-4">
          {{ editingBankAccount ? 'Edit Bank Account' : 'Add New Bank Account' }}
        </h4>
        
        <form @submit.prevent="submitBankAccountForm" class="space-y-4">
          <!-- Bank Account Name -->
          <div>
            <label class="block text-gray-300 mb-1 text-sm">Account Name *</label>
            <input 
              type="text" 
              v-model="bankAccountForm.name" 
              class="w-full bg-gray-800 text-white border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:border-purple-500"
              placeholder="e.g., Main Checking Account"
              :class="{ 'border-red-500': bankAccountValidationErrors.name }"
            >
            <p v-if="bankAccountValidationErrors.name" class="text-red-500 text-xs mt-1">{{ bankAccountValidationErrors.name }}</p>
          </div>
          
          <!-- IBAN -->
          <div>
            <label class="block text-gray-300 mb-1 text-sm">IBAN *</label>
            <input 
              type="text" 
              v-model="bankAccountForm.iban" 
              class="w-full bg-gray-800 text-white border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:border-purple-500"
              placeholder="e.g., DE89 3704 0044 0532 0130 00"
              :class="{ 'border-red-500': bankAccountValidationErrors.iban }"
            >
            <p v-if="bankAccountValidationErrors.iban" class="text-red-500 text-xs mt-1">{{ bankAccountValidationErrors.iban }}</p>
          </div>
          
          <!-- Description -->
          <div>
            <label class="block text-gray-300 mb-1 text-sm">Description</label>
            <textarea 
              v-model="bankAccountForm.description" 
              class="w-full bg-gray-800 text-white border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:border-purple-500"
              placeholder="Optional description for this account"
              rows="2"
            ></textarea>
          </div>
          
          <!-- Form Actions -->
          <div class="flex justify-end space-x-3 pt-2">
            <button 
              v-if="editingBankAccount"
              type="button"
              @click="cancelBankAccountEdit"
              class="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 text-sm rounded-md transition duration-200"
            >
              Cancel
            </button>
            
            <button 
              type="submit"
              class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-sm rounded-md transition duration-200 flex items-center"
              :disabled="isBankAccountSubmitting"
            >
              <span v-if="isBankAccountSubmitting" class="mr-2">
                <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </span>
              {{ editingBankAccount ? 'Update Account' : 'Add Account' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, watch, computed, onMounted } from 'vue';
import axios from 'axios';

export default {
  name: 'UserForm',
  props: {
    users: {
      type: Array,
      required: true
    }
  },
  emits: ['submit-success', 'close', 'error'],
  
  setup(props, { emit }) {
    const selectedUserId = ref('');
    const formData = reactive({
      id: null,
      name: '',
      email: ''
    });
    
    const isSubmitting = ref(false);
    const validationErrors = reactive({
      name: '',
      email: ''
    });
    
    // Bank accounts
    const bankAccounts = ref([]);
    const bankAccountForm = reactive({
      id: null,
      name: '',
      iban: '',
      description: '',
      user_id: null
    });
    const bankAccountValidationErrors = reactive({
      name: '',
      iban: ''
    });
    const isBankAccountSubmitting = ref(false);
    const editingBankAccount = ref(false);
    
    // Computed property to determine if we're in edit mode
    const isEditMode = computed(() => !!formData.id);
    
    // Fetch bank accounts when a user is selected
    const fetchBankAccounts = async (userId) => {
      try {
        const response = await axios.get(`/api/v1/bank_accounts/user/${userId}`);
        if (response.data.status === 'success') {
          bankAccounts.value = response.data.data;
        }
      } catch (error) {
        console.error('Error fetching bank accounts:', error);
        emit('error', `Failed to load bank accounts: ${error.response?.data?.message || error.message}`);
      }
    };
    
    // Handle user selection from dropdown
    const handleUserSelect = () => {
      // Reset validation errors
      Object.keys(validationErrors).forEach(key => {
        validationErrors[key] = '';
      });
      
      if (!selectedUserId.value) {
        // Create new user mode
        formData.id = null;
        formData.name = '';
        formData.email = '';
        bankAccounts.value = [];
        resetBankAccountForm();
        return;
      }
      
      // Find selected user and populate form data
      const selectedUser = props.users.find(user => user.id === parseInt(selectedUserId.value));
      if (selectedUser) {
        formData.id = selectedUser.id;
        formData.name = selectedUser.name;
        formData.email = selectedUser.email;
        
        // Fetch bank accounts for this user
        fetchBankAccounts(selectedUser.id);
      }
    };
    
    // Validate user form
    const validateForm = () => {
      let isValid = true;
      
      // Reset errors
      Object.keys(validationErrors).forEach(key => {
        validationErrors[key] = '';
      });
      
      if (!formData.name.trim()) {
        validationErrors.name = 'Name is required';
        isValid = false;
      }
      
      if (!formData.email.trim()) {
        validationErrors.email = 'Email is required';
        isValid = false;
      } else if (!/^\S+@\S+\.\S+$/.test(formData.email)) {
        validationErrors.email = 'Please enter a valid email address';
        isValid = false;
      }
      
      return isValid;
    };
    
    // Validate bank account form
    const validateBankAccountForm = () => {
      let isValid = true;
      
      // Reset errors
      Object.keys(bankAccountValidationErrors).forEach(key => {
        bankAccountValidationErrors[key] = '';
      });
      
      if (!bankAccountForm.name.trim()) {
        bankAccountValidationErrors.name = 'Account name is required';
        isValid = false;
      }
      
      if (!bankAccountForm.iban.trim()) {
        bankAccountValidationErrors.iban = 'IBAN is required';
        isValid = false;
      } else if (!/^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$/.test(bankAccountForm.iban.replace(/\s+/g, ''))) {
        bankAccountValidationErrors.iban = 'Please enter a valid IBAN';
        isValid = false;
      }
      
      return isValid;
    };
    
    // Submit user form
    const submitForm = async () => {
      if (!validateForm()) {
        return;
      }
      
      isSubmitting.value = true;
      
      try {
        let response;
        
        if (isEditMode.value) {
          // Update existing user
          response = await axios.put(`/api/v1/users/${formData.id}`, {
            name: formData.name,
            email: formData.email
          });
        } else {
          // Create new user
          response = await axios.post('/api/v1/users/', {
            name: formData.name,
            email: formData.email
          });
        }
        
        if (response.data.status === 'success') {
          emit('submit-success', {
            type: isEditMode.value ? 'update' : 'create',
            user: response.data.data
          });
          
          if (!isEditMode.value) {
            // If we just created a user, switch to edit mode
            formData.id = response.data.data.id;
            selectedUserId.value = response.data.data.id.toString();
          }
        }
      } catch (error) {
        console.error('User form submission error:', error);
        
        if (error.response && error.response.status === 409) {
          // Email already exists
          validationErrors.email = 'This email is already in use';
        } else {
          emit('error', `Failed to ${isEditMode.value ? 'update' : 'create'} user: ${error.response?.data?.message || error.message}`);
        }
      } finally {
        isSubmitting.value = false;
      }
    };
    
    // Edit bank account
    const editBankAccount = (account) => {
      bankAccountForm.id = account.id;
      bankAccountForm.name = account.name;
      bankAccountForm.iban = account.iban;
      bankAccountForm.description = account.description || '';
      bankAccountForm.user_id = formData.id;
      editingBankAccount.value = true;
    };
    
    // Cancel bank account edit
    const cancelBankAccountEdit = () => {
      resetBankAccountForm();
      editingBankAccount.value = false;
    };
    
    // Submit bank account form
    const submitBankAccountForm = async () => {
      if (!validateBankAccountForm()) {
        return;
      }
      
      isBankAccountSubmitting.value = true;
      
      try {
        let response;
        
        // Ensure IBAN is properly formatted (remove spaces)
        const formattedIban = bankAccountForm.iban.replace(/\s+/g, '');
        
        if (editingBankAccount.value) {
          // Update existing bank account
          response = await axios.put(`/api/v1/bank_accounts/${bankAccountForm.id}`, {
            name: bankAccountForm.name,
            iban: formattedIban,
            description: bankAccountForm.description,
            user_id: formData.id
          });
        } else {
          // Create new bank account
          response = await axios.post('/api/v1/bank_accounts/', {
            name: bankAccountForm.name,
            iban: formattedIban,
            description: bankAccountForm.description,
            user_id: formData.id
          });
        }
        
        if (response.data.status === 'success') {
          // Refresh the bank accounts list
          await fetchBankAccounts(formData.id);
          resetBankAccountForm();
          editingBankAccount.value = false;
          
          emit('submit-success', {
            type: editingBankAccount.value ? 'update-bank-account' : 'create-bank-account',
            bankAccount: response.data.data
          });
        }
      } catch (error) {
        console.error('Bank account form submission error:', error);
        
        if (error.response && error.response.status === 409) {
          // IBAN already exists
          bankAccountValidationErrors.iban = 'This IBAN is already registered';
        } else {
          emit('error', `Failed to ${editingBankAccount.value ? 'update' : 'create'} bank account: ${error.response?.data?.message || error.message}`);
        }
      } finally {
        isBankAccountSubmitting.value = false;
      }
    };
    
    // Confirm user deletion
    const confirmDeleteUser = async () => {
      if (confirm(`Are you sure you want to delete user ${formData.name}?`)) {
        isSubmitting.value = true;
        
        try {
          const response = await axios.delete(`/api/v1/users/${formData.id}`);
          
          if (response.data.status === 'success') {
            emit('submit-success', {
              type: 'delete',
              userId: formData.id
            });
            resetForm();
          }
        } catch (error) {
          console.error('User deletion error:', error);
          emit('error', `Failed to delete user: ${error.response?.data?.message || error.message}`);
        } finally {
          isSubmitting.value = false;
        }
      }
    };
    
    // Confirm bank account deletion
    const confirmDeleteBankAccount = async (account) => {
      if (confirm(`Are you sure you want to delete the bank account "${account.name}"?`)) {
        try {
          const response = await axios.delete(`/api/v1/bank_accounts/${account.id}`);
          
          if (response.data.status === 'success') {
            // Refresh the bank accounts list
            await fetchBankAccounts(formData.id);
            
            emit('submit-success', {
              type: 'delete-bank-account',
              bankAccountId: account.id
            });
          }
        } catch (error) {
          console.error('Bank account deletion error:', error);
          
          if (error.response && error.response.status === 400) {
            // Cannot delete account with transactions
            emit('error', 'Cannot delete bank account with associated transactions');
          } else {
            emit('error', `Failed to delete bank account: ${error.response?.data?.message || error.message}`);
          }
        }
      }
    };
    
    // Reset user form
    const resetForm = () => {
      selectedUserId.value = '';
      formData.id = null;
      formData.name = '';
      formData.email = '';
      
      Object.keys(validationErrors).forEach(key => {
        validationErrors[key] = '';
      });
      
      bankAccounts.value = [];
      resetBankAccountForm();
    };
    
    // Reset bank account form
    const resetBankAccountForm = () => {
      bankAccountForm.id = null;
      bankAccountForm.name = '';
      bankAccountForm.iban = '';
      bankAccountForm.description = '';
      bankAccountForm.user_id = formData.id;
      
      Object.keys(bankAccountValidationErrors).forEach(key => {
        bankAccountValidationErrors[key] = '';
      });
      
      editingBankAccount.value = false;
    };
    
    return {
      selectedUserId,
      formData,
      isSubmitting,
      validationErrors,
      isEditMode,
      handleUserSelect,
      submitForm,
      confirmDeleteUser,
      
      // Bank account related
      bankAccounts,
      bankAccountForm,
      bankAccountValidationErrors,
      isBankAccountSubmitting,
      editingBankAccount,
      editBankAccount,
      cancelBankAccountEdit,
      submitBankAccountForm,
      confirmDeleteBankAccount
    };
  }
};
</script>