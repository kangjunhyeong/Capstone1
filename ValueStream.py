"""
Copyright (c) 2023, Electric Power Research Institute

 All rights reserved.

 Redistribution and use in source and binary forms, with or without modification,
 are permitted provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.
     * Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.
     * Neither the name of DER-VET nor the names of its contributors
       may be used to endorse or promote products derived from this software
       without specific prior written permission.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
"""
ValueStreamream.py

This Python class contains methods and attributes specific for service analysis within StorageVet.
"""
import numpy as np
import cvxpy as cvx
import pandas as pd


class ValueStream:
    """ 제공 기술에 의해 제공되고 제약을 받는 서비스에 대한 일반적인 템플릿.
    """

    def __init__(self, name, params):
        """ 모든 서비스를 다음 속성으로 초기화합니다.

        Args:
            name (str): 서비스에 대한 문자열 이름/설명
            params (Dict): 입력 매개변수
        """
        self.name = name
        self.dt = params['dt']   # 시간 간격
        self.system_requirements = []   # 시스템 요구 사항 리스트

        self.variables_df = pd.DataFrame()  # 최적화 변수는 여기에 저장됨
        self.variable_names = {}  # 변수 이름

         # 최적화 문제에 특화된 속성 (창에서 창으로 변경될 수 있는 속성)
        self.variables = None

    def grow_drop_data(self, years, frequency, load_growth):
        """ 주어진 데이터를 성장시키거나 추가로 포함된 데이터를 삭제하여 데이터를 확장합니다. 성장 데이터를 추가한 후 최적화가 실행되기 전에 시계열 데이터를 보관하는 변수를 업데이트합니다.

        Args:
            years (List): 분석이 수행될 연도의 목록
            frequency (str): 시계열 데이터의 주기 또는 빈도
            load_growth (float): 이 시뮬레이션에서 부하 성장률의 백분율 또는 소수값

        """
        pass

    def calculate_system_requirements(self, der_lst):
        """ 다른 Value Stream이 활성화되는지 여부에 관계없이 충족되어야 하는 시스템 요구 사항을 계산합니다. 그러나 이러한 요구 사항은 분석 중에 활성화된 기술에 따라 달라집니다.

        Args:
            der_lst (list): 시나리오에서 초기화된 DER(Distributed Energy Resource) 목록
        """
        pass

    def initialize_variables(self, size):
        """ 새로운 최적화 변수를 생성하지 않는 기본 메서드입니다.

        Args:
            size (int): 생성할 최적화 변수의 길이

        """
    def p_reservation_charge_up(self, mask):
        """ 이 Value Stream에 대한 예약해야 하는 위 방향(그리드로 전원을 제공하는 방향)으로의 충전 전력 양입니다.


        Args:
            mask (DataFrame): subs 데이터 세트에 포함된 time_series 데이터에 해당하는 인덱스에 대해 true인 부울 배열
        Returns: CVXPY parameter/variable

        """
        return cvx.Parameter(value=np.zeros(sum(mask)), shape=sum(mask), name=f'{self.name}ZeroUp')

    def p_reservation_charge_down(self, mask):
        """ 이 Value Stream에 대한 예약해야 하는 아래 방향(그리드에서 전원을 가져오는 방향)으로의 충전 전력 양입니다.

        Args:
            mask (DataFrame): subs 데이터 세트에 포함된 time_series 데이터에 해당하는 인덱스에 대해 true인 부울 배열
        Returns: CVXPY parameter/variable

        """
        return cvx.Parameter(value=np.zeros(sum(mask)), shape=sum(mask), name=f'{self.name}ZeroDown')

    def p_reservation_discharge_up(self, mask):
        """ 이 Value Stream에 대한 예약해야 하는 위쪽 방향(그리드로 전원을 제공하는 방향)으로의 방전 전력 양입니다.

        Args:
            mask (DataFrame):subs 데이터 세트에 포함된 time_series 데이터에 해당하는 인덱스에 대해 true인 부울 배열
        Returns: CVXPY parameter/variable

        """
        return cvx.Parameter(value=np.zeros(sum(mask)), shape=sum(mask), name=f'{self.name}ZeroUp')

    def p_reservation_discharge_down(self, mask):
        """ 이 Value Stream에 대한 예약해야 하는 아래쪽 방향(그리드에서 전원을 가져오는 방향)으로의 방전 전력 양입니다.

        Args:
            mask (DataFrame): subs 데이터 세트에 포함된 time_series 데이터에 해당하는 인덱스에 대해 true인 부울 배열

        Returns: CVXPY parameter/variable

        """
        return cvx.Parameter(value=np.zeros(sum(mask)), shape=sum(mask), name=f'{self.name}ZeroDown')

    def uenergy_option_stored(self, mask):
        """ 이 Value Stream에 대한 예약해야 하는 변동 상승에 따른 에너지 양입니다.

        Args:
            mask (DataFrame): subs 데이터 세트에 포함된 time_series 데이터에 해당하는 인덱스에 대해 true인 부울 배열

        Returns: the up energy reservation in kWh

        """
        return cvx.Parameter(value=np.zeros(sum(mask)), shape=sum(mask), name=f'ZeroStored{self.name}')

    def uenergy_option_provided(self, mask):
        """ 이 Value Stream 에 대한 변 상승에 따른 예약된 상승 에너지 양입니다.

        Args:
            mask (DataFrame): subs 데이터 세트에 포함된 time_series 데이터에 해당하는 인덱스에 대해 true인 부울 배열

        Returns: the up energy reservation in kWh

        """
        return cvx.Parameter(value=np.zeros(sum(mask)), shape=sum(mask), name=f'ZeroProvided{self.name}')

    def worst_case_uenergy_stored(self, mask):
        """ 현재 SOE로부터 예약되어야 하는 에너지 양으로, 시계열 데이터에 포함되지 않은 시간 단계 사이의 위반을 방지합니다.
            NOTE: 저장된 에너지는 양수이어야 하며, 제공된 에너지는 음수여야 합니다.

        Args:
            mask (DataFrame): subs 데이터 세트에 포함된 time_series 데이터에 해당하는 인덱스에 대해 true인 부울 배열

        Returns: 예상보다 많은 에너지로 시스템이 끝날 경우의 경우

        """
        stored = cvx.Parameter(value=np.zeros(sum(mask)), shape=sum(mask), name=f'uEstoredZero{self.name}')
        return stored

    def worst_case_uenergy_provided(self, mask):
        """ 현재 SOE로부터 예약되어야 하는 에너지 양으로, 시계열 데이터에 포함되지 않은 시간 단계 사이의 위반을 방지합니다.
            NOTE: 저장된 에너지는 양수이어야 하며, 제공된 에너지는 음수여야 합니다.

        Args:
            mask (DataFrame): subs 데이터 세트에 포함된 time_series 데이터에 해당하는 인덱스에 대해 true인 부울 배열
        Returns: 예상상보다 적은 에너지로 시스템이 끝날 경우의 경우

        """
        provided = cvx.Parameter(value=np.zeros(sum(mask)), shape=sum(mask), name=f'uEprovidedZero{self.name}')
        return provided

    def objective_function(self, mask, load_sum, tot_variable_gen, generator_out_sum, net_ess_power, annuity_scalar=1):
        """ 전체 목적 함수를 생성하며 최적화 변수를 포함합니다.

        Args:
            mask (DataFrame): subs 데이터 세트에 포함된 time_series 데이터에 해당하는 인덱스에 대해 true인 부울 배열
        tot_variable_gen (Expression): 변수/불규칙 발전원의 합
        load_sum (list, Expression): 시스템 내의 부하 합계
        generator_out_sum (list, Expression): 시스템 내의 일반적인 발전의 합계
        net_ess_power (list, Expression): 시스템 내의 모든 ESS의 순 전력 합계 [= 충전 - 방전]
        annuity_scalar (float): 프로젝트 수명 동안 비용 또는 이익을 포착하는 데 사용되는 연간 비용 또는 이익에 곱해질 스칼라 값 (사이징인 경우에만 설정)

        Returns:
            표현식의 키로 레이블이 지정된 목적 함수의 영향 부분을 나타내는 딕셔너리. 기본값은 {}를 반환합니다.

    def constraints(self, mask, load_sum, tot_variable_gen, generator_out_sum, net_ess_power, combined_rating):
        """Default build constraint list method. Used by services that do not have constraints.

        Args:
            mask (DataFrame): A boolean array that is true for indices corresponding to time_series data included
                    in the subs data set
            tot_variable_gen (Expression): the sum of the variable/intermittent generation sources
            load_sum (list, Expression): the sum of load within the system
            generator_out_sum (list, Expression): the sum of conventional generation within the system
            net_ess_power (list, Expression): the sum of the net power of all the ESS in the system. [= charge - discharge]
            combined_rating (cvx.Expression, int): the combined rating of DER that can reliabily dispatched in a worst case situtation
                these usually tend to be ESS and Generators

        Returns:
            An empty list (for aggregation of later constraints)
        """
        return []

    def save_variable_results(self, subs_index):
        """ Searches through the dictionary of optimization variables_df and saves the ones specific to each
        ValueStream instance and saves the values it to itself

        Args:
            subs_index (Index): index of the subset of data for which the variables_df were solved for

        """
        variable_values = pd.DataFrame({name: self.variables[name].value for name in self.variable_names}, index=subs_index)
        self.variables_df = pd.concat([self.variables_df, variable_values], sort=True)

    def timeseries_report(self):
        """ Summaries the optimization results for this Value Stream.

        Returns: A timeseries dataframe with user-friendly column headers that summarize the results
            pertaining to this instance

        """

    def monthly_report(self):
        """  Collects all monthly data that are saved within this object

        Returns: A dataframe with the monthly input price of the service

        """

    def drill_down_reports(self, monthly_data=None, time_series_data=None, technology_summary=None, **kwargs):
        """ Calculates any service related dataframe that is reported to the user.

        Returns: dictionary of DataFrames of any reports that are value stream specific
            keys are the file name that the df will be saved with

        """
        return {}

    def update_price_signals(self, monthly_data, time_series_data):
        """ Updates attributes related to price signals with new price signals that are saved in
        the arguments of the method. Only updates the price signals that exist, and does not require all
        price signals needed for this service.

        Args:
            monthly_data (DataFrame): monthly data after pre-processing
            time_series_data (DataFrame): time series data after pre-processing

        """
        pass

    def proforma_report(self, opt_years, apply_inflation_rate_func, fill_forward_func, results):
        """ Calculates the proforma that corresponds to participation in this value stream

        Args:
            opt_years (list): list of years the optimization problem ran for
            apply_inflation_rate_func:
            fill_forward_func:
            results (pd.DataFrame): DataFrame with all the optimization variable solutions

        Returns: A tuple of a DateFrame (of with each year in opt_year as the index and the corresponding
        value this stream provided)

        """
        opt_years = [pd.Period(year=item, freq='y') for item in opt_years]
        proforma = pd.DataFrame(index=opt_years)
        return proforma

    def min_regulation_up(self):
        return 0

    def min_regulation_down(self):
        return 0

    def max_participation_is_defined(self):
        return False

    def rte_list(self, poi):
        # value streams sometimes need rte in calculations
        # get a list of rte values from all active ess
        # default to [1], so that division by rte remains valid
        rte_list = [der.rte for der in poi.der_list if der.technology_type == 'Energy Storage System']
        if len(rte_list) == 0:
            rte_list = [1]
        # set an attribute to the value stream
        self.rte_list = rte_list
