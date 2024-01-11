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
ResourceAdequacy.py

이 Python 클래스에는 StorageVet 내의 서비스 분석에 특정한 메서드와 속성이 포함되어 있습니다.
"""
from storagevet.ValueStreams.ValueStream import ValueStream
import pandas as pd
import numpy as np
from storagevet.SystemRequirement import Requirement
import storagevet.Library as Lib


class ResourceAdequacy(ValueStream):
    """ 자원 충분성(ValueStream) 값 스트림. 각 서비스는 PreDispService 클래스의 하위 클래스가 될 것입니다.
    """

    def __init__(self, params):
        """ 목적 함수를 생성하고 제약 조건을 찾고 생성합니다.

          Args:
            params (Dict): 입력 매개변수

        """

        # 일반적인 서비스 객체를 생성합니다
        ValueStream.__init__(self, 'Resource Adequacy', params)

        # RA 특정 속성을 추가합니다.
        self.days = params['days']  # 피크 이벤트의 일수
        self.length = params['length']  # 방전 기간
        self.idmode = params['idmode'].lower()  # 피크 선택 모드
        self.dispmode = params['dispmode']  # 디스패치 모드
        self.capacity_rate = params['value']  # 월간 RA 용량 요금 (길이 = 12)
        if 'active hours' in self.idmode:
            self.active = params['active'] == 1  # 활성 RA 타임스텝 (길이 = 8760/dt)은 불리언
        self.system_load = params['system_load']  # 시스템 부하 프로필 (길이 = 8760/dt)
        self.growth = params['growth'] / 100  # RA 가격의 성장률, %에서 십진수로 변환

        # 나중에 설정될 다음 속성을 초기화합니다.
        self.peak_intervals = []
        self.event_intervals = None
        self.event_start_times = None
        self.der_dispatch_discharge_min_constraint = None
        self.energy_min_constraint = None
        self.qc = 0

    def grow_drop_data(self, years, frequency, load_growth):
        """ 주어진 데이터를 성장시키거나 추가된 데이터를 제거 / 성장 데이터를 추가한 후에는 최적화가 실행되기 전에 이 메서드를 호출

        Args:
            years (List): 분석이 수행될 연도 목록
            frequency (str): 시계열 데이터의 주기
            load_growth (float): 시뮬레이션에서 부하 성장률의 퍼센트/소수값
        """
        # 시계열 데이터
        self.system_load = Lib.fill_extra_data(self.system_load, years, load_growth, frequency)
        self.system_load = Lib.drop_extra_data(self.system_load, years)

        if 'active hours' in self.idmode:
            self.active = Lib.fill_extra_data(self.active, years, 0, frequency)
            self.active = Lib.drop_extra_data(self.active, years)
            self.active = self.active == 1

        # 월간 데이터
        self.capacity_rate = Lib.fill_extra_data(self.capacity_rate, years, 0, 'M')
        self.capacity_rate = Lib.drop_extra_data(self.capacity_rate, years)

    def calculate_system_requirements(self, der_lst):
        """ 다른 값 스트림이 활성화되었는지 여부에 관계없이 충족되어야 하는 시스템 요구사항을 계산/ 그러나 이러한 요구사항은 분석에서 활성화된 기술에 따라 달라.

        Args:
            der_lst (list): 시나리오에서 초기화된 DER(Distributed Energy Resources) 목록
        """
       # 시스템 부하 피크 찾기
        self.find_system_load_peaks()
       # 이벤트 스케줄 생성
        self.schedule_events()
       # 자격 요구사항 계산
        self.qc = self.qualifying_commitment(der_lst, self.length)
        total_time_intervals = len(self.event_intervals)

        if self.dispmode:
            # 디스패치 파워 제약 생성
            # 순 전력은 RA 이벤트에 해당하는 시간에 자격 요구사항이어야 합니다.

            self.der_dispatch_discharge_min_constraint = pd.Series(np.repeat(self.qc, total_time_intervals), index=self.event_intervals,
                                                      name='RA Discharge Min (kW)')
            self.system_requirements += [Requirement('der dispatch discharge', 'min', self.name, self.der_dispatch_discharge_min_constraint)]
        else:
            # 에너지 예약 제약 생성
            qualifying_energy = self.qc * self.length

            # 에너지는 RA 이벤트의 시작에서 최소한 자격 에너지 값이어야 하며, 이를 통해 약속을 이벤트 전체 동안 충족할 충분한 에너지가 있는지 확인합니다.
            self.energy_min_constraint = pd.Series(np.repeat(qualifying_energy, len(self.event_start_times)), index=self.event_start_times,
                                                   name='RA Energy Min (kWh)')
            self.system_requirements.append(Requirement('energy', 'min', self.name, self.energy_min_constraint))

    def find_system_load_peaks(self):
        """ 시스템 부하 피크가 발생하는 타임스텝을 찾습니다. RA 이벤트는 이러한 피크 주변에 발생합니다.
            이 메서드는 PEAK_INTERVALS 속성을 편집합니다.
        """
        for year in self.system_load.index.year.unique():
            year_o_system_load = self.system_load.loc[self.system_load.index.year == year]
            if self.idmode == 'peak by year':
                # 1) 시스템 부하를 가장 큰 것부터 가장 작은 것으로 정렬
                max_int = year_o_system_load.sort_values(ascending=False)
                 # 2) 하루에 한 번씩만 나타나는 첫 번째(즉, 가장 큰) 인스턴트 로드만 유지 
                 # 이미 인덱스에 나타난 항목에 대해 True인 불리언 배열을 사용
                max_int_date = pd.Series(max_int.index.date, index=max_int.index)
                max_days = max_int.loc[~max_int_date.duplicated(keep='first')]

                # 3) 피크 타임스텝 선택
                # system_load가 피크인 이벤트 수를 찾습니다.
                # 처음 DAYS 타임스텝만 선택합니다.
                self.peak_intervals += list(max_days.index[:self.days].values)

            elif self.idmode == 'peak by month':
                # 1) 시스템 부하를 가장 큰 것부터 가장 작은 것으로 정렬
                max_int = year_o_system_load.sort_values(ascending=False)
                # 2) 하루에 한 번씩만 나타나는 첫 번째(즉, 가장 큰) 인스턴트 로드만 유지 
                # 이미 인덱스에 나타난 항목에 대해 True인 불리언 배열을 사용
                max_int_date = pd.Series(max_int.index.date, index=max_int.index)
                max_days = max_int.loc[~max_int_date.duplicated(keep='first')]

                # 3) 피크 타임스텝 선택
                # system_load가 피크인 이벤트 수를 찾습니다.
                # 각 월별로 DAYS 타임스텝만 선택합니다.
                self.peak_intervals += list(max_days.groupby(by=max_days.index.month).head(self.days).index.values)

            elif self.idmode == 'peak by month with active hours':
                active_year_sub = self.active[self.system_load.index.year == year]
                # 1) 시스템 부하를 활성 시간 동안 가장 큰 것부터 가장 작은 것으로 정렬
                max_int = year_o_system_load.loc[active_year_sub].sort_values(ascending=False)
                # 2) 하루에 한 번씩만 나타나는 첫 번째(즉, 가장 큰) 인스턴트 로드만 유지 
                # 이미 인덱스에 나타난 항목에 대해 True인 불리언 배열을 사용
                max_int_date = pd.Series(max_int.index.date, index=max_int.index)
                max_days = max_int.loc[~max_int_date.duplicated(keep='first')]

               # 3) 피크 타임스텝 선택
               # 시스템 부하가 활성 시간 동안 피크인 이벤트 수를 찾는다.
               # 각 월별로 DAYS 타임스텝만 선택
                self.peak_intervals += list(max_days.groupby(by=max_days.index.month).head(self.days).index.values)

    def schedule_events(self):
        """ RA 이벤트 간격 및 이벤트 시작 시간을 결정합니다.

         TODO: 고려해야 할 예외 상황 -- 이벤트가 최적화 창의 시작이나 끝에 발생하는 경우 -- HN
         TODO: 이것이 sub-hourly 시스템 부하 프로파일에 대해 작동하는지 확인 -- HN

        """
        # DETERMINE RA EVENT INTERVALS
        event_interval = pd.Series(np.zeros(len(self.system_load)), index=self.system_load.index)
        event_start = pd.Series(np.zeros(len(self.system_load)), index=self.system_load.index)  # used to set energy constraints
        # odd intervals straddle peak & even intervals have extra interval after peak
        steps = self.length / self.dt
        if steps % 2:  # this is true if mod(steps/2) is not 0 --> if steps is odd
            presteps = np.floor_divide(steps, 2)
        else:  # steps is even
            presteps = (steps / 2) - 1
        poststeps = presteps + 1

        for peak in self.peak_intervals:
            first_int = peak - pd.Timedelta(presteps * self.dt, unit='h')
            last_int = peak + pd.Timedelta(poststeps * self.dt, unit='h')

            # handle edge RA event intervals
            if first_int < event_interval.index[0]:  # RA event starts before the first time-step in the system load
                first_int = event_interval.index[0]
            if last_int > event_interval.index[-1]:  # RA event ends after the last time-step in the system load
                last_int = event_interval.index[-1]

            event_range = pd.date_range(start=first_int, end=last_int, periods=steps)
            event_interval.loc[event_range] = 1
            event_start.loc[first_int] = 1
        self.event_intervals = self.system_load[event_interval == 1].index
        self.event_start_times = self.system_load[event_start == 1].index

    @staticmethod
    def qualifying_commitment(der_lst, length):
        """

        Args:
            der_lst (list): list of the initialized DERs in our scenario
            length (int): length of the event

        NOTE: DR has this same method too  -HN

        """
        qc = sum(der_instance.qualifying_capacity(length) for der_instance in der_lst)
        return qc

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
        proforma = ValueStream.proforma_report(self, opt_years, apply_inflation_rate_func,
                                               fill_forward_func, results)
        proforma[self.name + ' Capacity Payment'] = 0

        for year in opt_years:
            proforma.loc[pd.Period(year=year, freq='y')] = self.qc * np.sum(self.capacity_rate)
        # apply inflation rates
        proforma = apply_inflation_rate_func(proforma, None, min(opt_years))
        proforma = fill_forward_func(proforma, self.growth)
        return proforma

    def timeseries_report(self):
        """ Summaries the optimization results for this Value Stream.

        Returns: A timeseries dataframe with user-friendly column headers that summarize the results
            pertaining to this instance

        """
        report = pd.DataFrame(index=self.system_load.index)
        report.loc[:, "System Load (kW)"] = self.system_load
        report.loc[:, 'RA Event (y/n)'] = False
        report.loc[self.event_intervals, 'RA Event (y/n)'] = True
        if self.dispmode:
            report = pd.merge(report, self.der_dispatch_discharge_min_constraint, how='left', on='Start Datetime (hb)')
        else:
            report = pd.merge(report, self.energy_min_constraint, how='left', on='Start Datetime (hb)')
        return report

    def monthly_report(self):
        """  Collects all monthly data that are saved within this object

        Returns: A dataframe with the monthly input price of the service

        """

        monthly_financial_result = pd.DataFrame({'RA Capacity Price ($/kW)': self.capacity_rate}, index=self.capacity_rate.index)
        monthly_financial_result.index.names = ['Year-Month']

        return monthly_financial_result

    def update_price_signals(self, monthly_data, time_series_data):
        """ Updates attributes related to price signals with new price signals that are saved in
        the arguments of the method. Only updates the price signals that exist, and does not require all
        price signals needed for this service.

        Args:
            monthly_data (DataFrame): monthly data after pre-processing
            time_series_data (DataFrame): time series data after pre-processing

        """
        try:
            self.capacity_rate = monthly_data.loc[:, 'RA Capacity Price ($/kW)']
        except KeyError:
            pass
