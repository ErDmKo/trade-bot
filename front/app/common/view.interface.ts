import { IBaseBalance } from './api.interface'

export interface IViewBalance extends IBaseBalance {
    funds?: Array<{
        amount: string,
        name: string
    }>
}
