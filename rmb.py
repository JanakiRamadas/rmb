from flask import Flask, request, url_for, redirect, session, render_template, json, flash, send_file, jsonify
from flask_session import Session


import requests
from urllib.request import urlopen
import json
import math
#hello sample modification

rmb = Flask(__name__)
rmb.config["SESSION_PERMANENT"] = False
rmb.config["SESSION_TYPE"] = "filesystem"
rmb.config['SECRET_KEY'] = b'1db9a6ffaf6a8566338d6d2f8db1f812a7c23a4e25299ab6ab228a81e9cfdaf0'
rmb.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Recommended for security
rmb.config['SESSION_COOKIE_SECURE'] = True # Use True in production with HTTPS
Session(rmb)
Session(rmb)
global target_emi_slm
global principalAmount
global loanTenure
global slmRate
#
def calculate_slm_emi(principal, slm_annual_rate, tenure_years):
	global target_emi_slm
	"""
	Calculates the Equated Monthly Installment (EMI) using the Straight Line Method (SLM).
	"""
	total_interest_slm = principal * slm_annual_rate * tenure_years
	total_repayable_amount = principal + total_interest_slm
	total_installments = tenure_years * 12
	emi_slm = total_repayable_amount / total_installments
	return emi_slm

def f(r_monthly, principal, num_installments, target_emi_slm):
	
	"""
	The function for which we need to find the root (f(r) = 0).
	It represents the difference between RBM EMI and target SLM EMI.
	r_monthly is the monthly interest rate (decimal).
	"""
	if r_monthly == 0:
		# Handle the case where r is zero to avoid division by zero or infinite loops
		# If r is 0, EMI = Principal / N
		return (principal / num_installments) - target_emi_slm
	
	# Standard EMI formula for Reducing Balance Method
	numerator = r_monthly * (1 + r_monthly)**num_installments
	denominator = (1 + r_monthly)**num_installments - 1
	
	if denominator == 0: # Should ideally not happen with positive rates and installments
		return float('inf') # Indicate a problem

	rbm_emi = principal * (numerator / denominator)
	return rbm_emi - target_emi_slm

def f_prime(r_monthly, principal, num_installments):
	"""
	The derivative of the function f(r) with respect to r.
	This derivative is for the RBM EMI formula part: P * [r(1+r)^N] / [(1+r)^N - 1]
	"""
	N = num_installments
	P = principal

	# Simplifications for the derivative
	term_a = (1 + r_monthly)**N
	term_b = N * (1 + r_monthly)**(N - 1)

	# Numerator of the derivative of [r * (1+r)^N] / [(1+r)^N - 1]
	u_prime_v = (term_a + r_monthly * term_b) * (term_a - 1)
	u_v_prime = (r_monthly * term_a) * term_b

	# Denominator of the derivative
	v_squared = (term_a - 1)**2
	
	if v_squared == 0: # Avoid division by zero
		return float('inf')

	derivative_rbm_emi = P * (u_prime_v - u_v_prime) / v_squared
	return derivative_rbm_emi


def newton_raphson_rbm_rate(principal, slm_annual_rate, tenure_years, initial_guess=0.01, tolerance=1e-7, max_iterations=1000):
	global target_emi_slm
	"""
	Uses the Newton-Raphson method to find the equivalent RBM annual interest rate.

	Args:
		principal (float): The principal loan amount.
		slm_annual_rate (float): The annual interest rate in SLM (as a decimal, e.g., 0.10 for 10%).
		tenure_years (int): The loan tenure in years.
		initial_guess (float): An initial guess for the monthly RBM interest rate (decimal).
								A good starting point is usually a small positive value like 0.01.
		tolerance (float): The maximum acceptable difference between successive approximations.
		max_iterations (int): Maximum number of iterations to prevent infinite loops.

	Returns:
		float: The annual RBM interest rate (as a decimal) or None if not converged.
	"""
	if principal <= 0 or slm_annual_rate < 0 or tenure_years <= 0:
		raise ValueError("Principal, SLM Rate, and Tenure must be positive values.")
	
	num_installments = tenure_years * 12
	target_emi_slm = calculate_slm_emi(principal, slm_annual_rate, tenure_years)

	r_n = initial_guess # Current approximation for monthly RBM rate

	print(f"Target EMI (SLM Equivalent): {target_emi_slm:,.2f}")
	print("\n--- Newton-Raphson Iterations ---")
	
	for i in range(max_iterations):
		f_val = f(r_n, principal, num_installments, target_emi_slm)
		f_prime_val = f_prime(r_n, principal, num_installments)

		# Handle cases where derivative is zero or very close to zero
		if abs(f_prime_val) < 1e-10: # A very small number to check for near-zero derivative
			print(f"Iteration {i}: Derivative is too close to zero. Cannot converge.")
			return None
		
		# Calculate next approximation
		r_n_plus_1 = r_n - (f_val / f_prime_val)

		print(f"Iteration {i+1}: r_n = {r_n:.6f}, f(r_n) = {f_val:.4f}, f'(r_n) = {f_prime_val:.4f}, Next r = {r_n_plus_1:.6f}")

		# Check for convergence
		if abs(r_n_plus_1 - r_n) < tolerance:
			print(f"\nConverged after {i+1} iterations.")
			return r_n_plus_1 * 12 # Convert monthly rate to annual

		r_n = r_n_plus_1
		
		# Add a check for unrealistic rates (e.g., negative or excessively high)
		if r_n < -1 or r_n > 5: # Monthly rate usually doesn't go below -100% or above 500%
			print(f"Iteration {i}: Monthly rate became unrealistic ({r_n*100:.2f}%). Diverging or bad initial guess.")
			return None


	print("\nMax iterations reached. Did not converge within tolerance.")
	return None
#

#
@rmb.route('/SLMtoRBM', methods=['GET', 'POST'])
def SLMtoRBM():
	global target_emi_slm
	global principalAmount
	global loanTenure
	global slmRate
	target_emi_slm=0.0
	result_rbm = 0.0
	if request.method == 'POST':
			principalAmount = request.form['principalAmount']
			principal_amount = float(principalAmount)
			slmRate = request.form['slmRate']
			slm_rate_percent = float(slmRate)
			loanTenure = request.form['loanTenure']
			loan_tenure_years = float(loanTenure)
			slm_annual_rate_decimal = slm_rate_percent / 100
			rbm_annual_rate_decimal = newton_raphson_rbm_rate(
				principal=principal_amount,
				slm_annual_rate=slm_annual_rate_decimal,
				tenure_years=loan_tenure_years
			)
			if rbm_annual_rate_decimal is not None:
				print(f"\n--- Results ---")
				print(f"Principal: {principal_amount:,.2f}")
				print(f"SLM Annual Rate: {slm_rate_percent:.2f}%")
				print(f"Tenure: {loan_tenure_years} years")
				print(f"Equivalent RBM Annual Rate: {rbm_annual_rate_decimal * 100:.4f}%")
				result_rbm = rbm_annual_rate_decimal * 100
			else:
				print("\nCould not find an equivalent RBM rate. Please check inputs or adjust initial guess/tolerance.")
			
			return render_template('SLMtoRBM.html',principalAmount_str=principalAmount,
				slmRate=slmRate,loanTenure=loanTenure,target_emi_slm=round(target_emi_slm,2), result_rbm=round(result_rbm,2))
	else:
		return render_template('SLMtoRBM.html')
	return render_template('SLMtoRBM.html')






if __name__ == '__main__':
	#from waitress import serve
	#import logging
	#print("rmb is now running through Waitress WSGI")
	#serve(rmb, host="0.0.0.0", port=443)

	rmb.run(host='0.0.0.0', port=5000, debug = True)
	rmb.run(debug=True)



