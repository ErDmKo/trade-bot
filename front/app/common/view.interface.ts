import { IBalance, IBaseBalance } from './api.interface'

export interface IViewBalance extends IBaseBalance {
    funds?: Array<IBalance['funds'][string]>
}
