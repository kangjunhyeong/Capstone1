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
UserConstraints.py

This Python class contains methods and attributes specific for service analysis within StorageVet.
"""
from storagevet.ValueStreams.ValueStream import ValueStream
import pandas as pd
from storagevet.SystemRequirement import Requirement
import storagevet.Library as Lib
from storagevet.ErrorHandling import *
import numpy as np

VERY_LARGE_NUMBER = 2**32 - 1
VERY_LARGE_NEGATIVE_NUMBER = -1 * VERY_LARGE_NUMBER

class UserConstraints(ValueStream):
    """ 사용자가 입력한 시계열 제약 조건을 나타내는 클래스. 각 서비스는 PreDispService 클래스의 하위 클래스가 됩니다.
    """

    def __init__(self, params):
        """ 목적 함수를 생성하고 제약 조건을 찾아 생성합니다.

        Acceptable constraint names are: 'Power Max (kW)', 'Power Min (kW)', 'Energy Max (kWh)', 'Energy Min (kWh)'

          Args:
            params (Dict): 입력 매개변수
        """
        # 일반적인 서비스 객체 생성
        ValueStream.__init__(self, 'User Constraints', params)
     
        # 입력된 매개변수에서 사용자 제약 조건에 대한 정보 추출
        self.user_power = params['power']
        self.user_energy = params['energy']
        self.price = params['price']  # $/yr
        # 다양한 제약 조건을 초기화할 변수들
        self.poi_import_min_constraint = None
        self.poi_import_max_constraint = None
        self.poi_export_min_constraint = None
        self.poi_export_max_constraint = None
        self.soe_min_constraint = None
        self.soe_max_constraint = None

    def grow_drop_data(self, years, frequency, load_growth):
        """ 주어진 데이터를 성장시키거나 불필요한 데이터를 삭제하여 데이터를 추가합니다. 최적화가 실행되기 전에 add_growth_data 이후에 이 메서드를 호출해야 하는 변수를 업데이트합니다.

        Args:
            years (List): 분석이 수행될 연도 목록
            frequency (str): 시계열 데이터의 주기
            load_growth (float): 시뮬레이션에서의 부하 성장률의 백분율 또는 십진

        """
     # 전력(Power) 데이터에 대해 불필요한 데이터를 추가하고 삭제합니다.
        self.user_power = Lib.fill_extra_data(self.user_power, years, 0, frequency)
        self.user_power = Lib.drop_extra_data(self.user_power, years)
     # 에너지(Energy) 데이터에 대해 불필요한 데이터를 추가하고 삭제합니다.
        self.user_energy = Lib.fill_extra_data(self.user_energy, years, 0, frequency)
        self.user_energy = Lib.drop_extra_data(self.user_energy, years)

    def calculate_system_requirements(self, der_lst):
        """ 활성화된 다양한 DER에 따라 무관하게 충족되어야 하는 시스템 요구 사항을 계산합니다.
        Args:
            der_lst (list): 시나리오에서 초기화된 DER(Distributed Energy Resources) 목록

        """
        # 전력에 대한 시스템 요구 사항 설정 (모든 값이 양수임을 보장하며 사용자가 값들을 제공하는 방식과 관계없이)
        # NOTE: 이로 인해 최소 제약 조건의 0 값에 대한 처리가 여기서 이루어집니다 (매우 큰 음수 값으로 대체)
        #       최대 제약 조건은 변경하지 마세요 (해당 0 값은 no-export 또는 no-import 경우를 제어하는 데 중요합니다)
    
        # POI: Max Export (kW) 제약 조건 설정
        self.poi_export_max_constraint = self.user_power.get('POI: Max Export (kW)')
        if self.poi_export_max_constraint is not None:
            self.poi_export_max_constraint = self.return_positive_values(self.poi_export_max_constraint)
            self.system_requirements.append(Requirement('poi export', 'max', self.name, self.poi_export_max_constraint))
         
        # POI: Min Export (kW) 제약 조건 설정
        self.poi_export_min_constraint = self.user_power.get('POI: Min Export (kW)')
        if self.poi_export_min_constraint is not None:
            self.poi_export_min_constraint = self.return_positive_values(self.poi_export_min_constraint)
            self.poi_export_min_constraint[self.poi_export_min_constraint == 0] = VERY_LARGE_NEGATIVE_NUMBER
            TellUser.info('In order for the POI: Min Export constraint to work, we modify values that are zero to be a very large negative number')
            self.system_requirements.append(Requirement('poi export', 'min', self.name, self.poi_export_min_constraint))
       
        # POI: Max Import (kW) 제약 조건 설정
        self.poi_import_max_constraint = self.user_power.get('POI: Max Import (kW)')
        if self.poi_import_max_constraint is not None:
            self.poi_import_max_constraint = self.return_positive_values(self.poi_import_max_constraint)
            self.system_requirements.append(Requirement('poi import', 'max', self.name, self.poi_import_max_constraint))

        # POI: Min Import (kW) 제약 조건 설정
        self.poi_import_min_constraint = self.user_power.get('POI: Min Import (kW)')
        if self.poi_import_min_constraint is not None:
            self.poi_import_min_constraint = self.return_positive_values(self.poi_import_min_constraint)
            self.poi_import_min_constraint[self.poi_import_min_constraint == 0] = VERY_LARGE_NEGATIVE_NUMBER
            TellUser.info('In order for the POI: Min Import constraint to work, we modify values that are zero to be a very large negative number')
            self.system_requirements.append(Requirement('poi import', 'min', self.name, self.poi_import_min_constraint))

       # 에너지에 대한 시스템 요구 사항 설정
       # Aggregate Energy Max (kWh) 제약 조건 설정
        self.soe_max_constraint = self.user_energy.get('Aggregate Energy Max (kWh)')
        if self.soe_max_constraint is not None:
            self.system_requirements.append(Requirement('energy', 'max', self.name, self.soe_max_constraint))
       # Aggregate Energy Min (kWh) 제약 조건 설정
        self.soe_min_constraint = self.user_energy.get('Aggregate Energy Min (kWh)')
        if self.soe_min_constraint is not None:
            self.system_requirements.append(Requirement('energy', 'min', self.name, self.soe_min_constraint))

    def timeseries_report(self):
        """ Summaries the optimization results for this Value Stream.

        Returns: A timeseries dataframe with user-friendly column headers that summarize the results
            pertaining to this instance

        """
        # use the altered system requirement constraints in the output time series
        # NOTE: we display export values as the negative of what they are in the constraint,
        #     since negative Net Power is actually positive Export Power
        if self.poi_export_max_constraint is not None:
            TellUser.info('For better alignment with "Net Power" in the output time series, we multiply POI: Max Export values by -1')
            self.user_power['POI: Max Export (kW)'] = self.poi_export_max_constraint * -1
        if self.poi_export_min_constraint is not None:
            TellUser.info('For better alignment with "Net Power" in the output time series, we multiply POI: Min Export values by -1')
            self.user_power['POI: Min Export (kW)'] = self.poi_export_min_constraint * -1
        if self.poi_import_max_constraint is not None:
            self.user_power['POI: Max Import (kW)'] = self.poi_import_max_constraint
        if self.poi_import_min_constraint is not None:
            self.user_power['POI: Min Import (kW)'] = self.poi_import_min_constraint
        # add 'User Constraints' label to beginning of each column name
        new_power_names = {original: f"{self.name} {original}" for original in self.user_power.columns}
        self.user_power.rename(columns=new_power_names, inplace=True)
        new_energy_names = {original: f"{self.name} {original}" for original in self.user_energy.columns}
        self.user_energy.rename(columns=new_energy_names, inplace=True)
        # concat energy and power together
        power_df = self.user_power if not self.user_power.empty else None
        energy_df = self.user_energy if not self.user_energy.empty else None
        report = pd.concat([power_df, energy_df], axis=1)
        return report

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
        proforma[self.name + ' Value'] = 0

        for year in opt_years:
            proforma.loc[pd.Period(year=year, freq='y')] = self.price
        # apply inflation rates
        proforma = apply_inflation_rate_func(proforma, None, min(opt_years))
        proforma = fill_forward_func(proforma, None)
        return proforma

    def update_yearly_value(self, new_value: float):
        """ Updates the attribute associated to the yearly value of this service. (used by CBA)

        Args:
            new_value (float): the dollar yearly value to be assigned for providing this service

        """
        self.price = new_value

    @staticmethod
    def return_positive_values(array):
        """ Given an array s.t. for all values >0 or for all values <0 is true,
        return an array whose values are always positive

        Args:
            array (pd.Series):

        Returns: Series, with its values changed

        """
        if (array > 0).any():
            return array
        else:
            return -1*array
